from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    root: Path
    inbox_dir: Path
    processed_dir: Path
    adb_serial: str
    camera_dir: str


def load_settings(config_path: Path) -> Settings:
    if not config_path.exists():
        raise SystemExit(f"Missing {config_path}. Copy config.example.json to config.json first.")

    root = config_path.parent.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))

    def resolve(value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else root / path

    return Settings(
        root=root,
        inbox_dir=resolve(config["paths"].get("inbox_dir", "inbox")),
        processed_dir=resolve(config["paths"].get("processed_dir", "processed")),
        adb_serial=config["pixel"].get("adb_serial", ""),
        camera_dir=config["pixel"].get("camera_dir", "/sdcard/DCIM/Camera"),
    )


def load_dotenv(root: Path) -> None:
    env_path = root / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ensure_dirs(settings: Settings) -> None:
    settings.inbox_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)


def get_adb_executable() -> str:
    # 1. Kiem tra trong bien moi truong (tu .env hoac he thong)
    adb_env = os.environ.get("ADB_PATH")
    if adb_env:
        adb_path = Path(adb_env)
        if adb_path.is_dir():
            adb_exe = adb_path / "adb.exe" if os.name == "nt" else adb_path / "adb"
            if adb_exe.exists():
                return str(adb_exe)
        elif adb_path.exists():
            return str(adb_path)

    # 2. Kiem tra trong PATH he thong hien tai
    system_adb = shutil.which("adb")
    if system_adb:
        return system_adb

    # 3. Tu dong do tim trong cac thu muc pho bien tren Windows
    if os.name == "nt":
        possible_paths = [
            Path(os.getcwd()) / "platform-tools" / "adb.exe",
            Path(os.getcwd()) / "adb.exe",
            Path(Path.home()) / "Downloads" / "platform-tools" / "adb.exe",
            Path("C:\\platform-tools\\adb.exe"),
            Path("C:\\Program Files (x86)\\Android\\android-sdk\\platform-tools\\adb.exe"),
            Path("C:\\Program Files\\Android\\android-sdk\\platform-tools\\adb.exe"),
            Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk" / "platform-tools" / "adb.exe",
        ]
        for path in possible_paths:
            if path.exists():
                # Them vao PATH tam thoi cua tien trinh de scrcpy cung tim thay adb
                os.environ["PATH"] = str(path.parent) + os.pathsep + os.environ.get("PATH", "")
                return str(path)
                
    return "adb" # fallback


def adb_command(settings: Settings, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    adb_exe = get_adb_executable()
    command = [adb_exe]
    if settings.adb_serial:
        command += ["-s", settings.adb_serial]
    command += list(args)
    
    # An cua so console den cua adb tren Windows
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0 # SW_HIDE
        creationflags = 0x08000000 # CREATE_NO_WINDOW
        
    return subprocess.run(
        command, 
        text=True, 
        capture_output=True, 
        check=check, 
        startupinfo=startupinfo, 
        creationflags=creationflags
    )


def device_epoch_seconds(settings: Settings) -> int:
    output = adb_command(settings, "shell", "date", "+%s", check=False).stdout.strip()
    try:
        return int(output.splitlines()[-1])
    except (TypeError, ValueError, IndexError):
        return int(time.time())


def latest_media_after(settings: Settings, patterns: list[str], min_epoch: int) -> str:
    pattern_text = " ".join(f"{settings.camera_dir}/{pattern}" for pattern in patterns)
    command = (
        f"for f in {pattern_text}; do "
        '[ -e "$f" ] || continue; '
        'mtime=$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f" 2>/dev/null); '
        f'[ "$mtime" -ge {min_epoch} ] && printf \'%s %s\\n\' "$mtime" "$f"; '
        "done | sort -nr | head -n 1 | cut -d' ' -f2-"
    )
    return adb_command(settings, "shell", command, check=False).stdout.strip()


def is_camera_open(settings: Settings) -> bool:
    try:
        # Lấy trạng thái activity đang hiển thị trên foreground để check GCamera
        output = adb_command(settings, "shell", "dumpsys activity resumed", check=False).stdout
        return "com.google.android.GoogleCamera" in output
    except Exception:
        return False


def capture_from_pixel(settings: Settings) -> Path:
    ensure_dirs(settings)
    capture_started_at = max(0, device_epoch_seconds(settings) - 5)
    
    # Chỉ gọi lệnh mở camera nếu camera chưa được mở sẵn trên foreground (giúp giữ nguyên mức zoom của người dùng)
    if not is_camera_open(settings):
        adb_command(settings, "shell", "am", "start", "-a", "android.media.action.STILL_IMAGE_CAMERA")
        time.sleep(3)
    else:
        time.sleep(0.5)
        
    # Gửi phím Volume Down (25) để chụp ảnh trên Google Camera
    adb_command(settings, "shell", "input", "keyevent", "25")

    latest = ""
    for _ in range(12):
        time.sleep(1)
        latest = latest_media_after(settings, ["*.jpg", "*.jpeg"], capture_started_at)
        if latest:
            break
    if not latest:
        raise RuntimeError("Pixel did not create a new photo. Check Camera focus/permissions and try again.")

    local_path = settings.inbox_dir / Path(latest).name
    adb_command(settings, "pull", latest, str(local_path))
    return local_path


def capture_video_from_pixel(settings: Settings, duration_seconds: int = 10) -> Path:
    ensure_dirs(settings)
    duration_seconds = max(1, min(duration_seconds, 300))
    recording_started_at = max(0, device_epoch_seconds(settings) - 5)
    
    # Chỉ gọi lệnh mở camera video nếu camera chưa được mở sẵn trên foreground
    if not is_camera_open(settings):
        adb_command(settings, "shell", "am", "start", "-a", "android.media.action.VIDEO_CAMERA")
        time.sleep(3)
    else:
        time.sleep(0.5)
        
    # Gửi phím Volume Down (25) để bắt đầu quay video
    adb_command(settings, "shell", "input", "keyevent", "25")
    time.sleep(duration_seconds)
    # Gửi phím Volume Down (25) để dừng quay video
    adb_command(settings, "shell", "input", "keyevent", "25")

    latest = ""
    for _ in range(20):
        time.sleep(1)
        latest = latest_media_after(settings, ["*.mp4", "*.3gp"], recording_started_at)
        if latest:
            break
    if not latest:
        raise RuntimeError("Pixel did not create a new video. Check Camera focus/permissions and try again.")

    local_path = settings.inbox_dir / Path(latest).name
    adb_command(settings, "pull", latest, str(local_path))
    return local_path


def pixel_media_path(settings: Settings, local_path: Path) -> str:
    return f"{settings.camera_dir.rstrip('/')}/{local_path.name}"


def delete_pixel_media(settings: Settings, local_path: Path) -> str:
    remote_path = pixel_media_path(settings, local_path)
    result = adb_command(settings, "shell", "rm", "-f", "--", remote_path, check=False)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "ADB delete failed").strip()
        raise RuntimeError(f"Could not delete Pixel media {remote_path}: {message}")
    adb_command(
        settings,
        "shell",
        "am",
        "broadcast",
        "-a",
        "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d",
        f"file://{remote_path}",
        check=False,
    )
    return remote_path


def print_devices(settings: Settings) -> None:
    print(adb_command(settings, "devices", check=False).stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture Pixel media for the Drive-first web app.")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("devices", help="List ADB devices")
    subparsers.add_parser("capture", help="Capture one photo and pull it into inbox")
    record = subparsers.add_parser("record", help="Record one video and pull it into inbox")
    record.add_argument("--duration", type=int, default=10)
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    load_dotenv(config_path.parent)
    settings = load_settings(config_path)

    if args.command == "devices":
        print_devices(settings)
    elif args.command == "capture":
        print(capture_from_pixel(settings))
    elif args.command == "record":
        print(capture_video_from_pixel(settings, args.duration))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
