from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
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


def adb_command(settings: Settings, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = ["adb"]
    if settings.adb_serial:
        command += ["-s", settings.adb_serial]
    command += list(args)
    return subprocess.run(command, text=True, capture_output=True, check=check)


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


def capture_from_pixel(settings: Settings) -> Path:
    ensure_dirs(settings)
    capture_started_at = max(0, device_epoch_seconds(settings) - 1)
    adb_command(settings, "shell", "am", "start", "-a", "android.media.action.STILL_IMAGE_CAMERA")
    time.sleep(2)
    adb_command(settings, "shell", "input", "keyevent", "27")

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
    recording_started_at = max(0, device_epoch_seconds(settings) - 1)
    adb_command(settings, "shell", "am", "start", "-a", "android.media.action.VIDEO_CAMERA")
    time.sleep(2)
    adb_command(settings, "shell", "input", "keyevent", "27")
    time.sleep(duration_seconds)
    adb_command(settings, "shell", "input", "keyevent", "27")

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
