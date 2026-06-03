import subprocess
import sys
import shutil
from pathlib import Path

def build():
    print("=== BAT DAU TIEN TRINH DONG GOI EXE ===")
    
    # 1. Kiem tra va cai dat PyInstaller
    try:
        import PyInstaller
        print("PyInstaller da duoc cai dat.")
    except ImportError:
        print("Dang cai dat PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("Cai dat PyInstaller thanh cong.")
        
    # 2. Xac dinh duong dan
    root = Path(__file__).resolve().parent
    web_app_py = root / "web_app.py"
    dist_dir = root / "dist" / "PixelDriveCapture"
    
    # Don dep thu muc build cu truoc de tranh loi thu muc khong rong
    if dist_dir.exists():
        print(f"Dang don dep thu muc cu tai: {dist_dir}...")
        try:
            shutil.rmtree(dist_dir)
        except Exception as e:
            print(f"Cai bao: Khong the xoa hoan toan thu muc dist cu (co the co file dang mo): {e}")
    
    # 3. Chay lenh PyInstaller
    # --onedir de tao ra thu muc phan phoi chua file exe và cac files config de nguoi dung sua truc tiep
    # --clean de don dep cache cu
    # --name thiet lap ten file run
    # --noconfirm de tu dong ghi de ma khong can xac nhan
    print("Dang chay PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=PixelDriveCapture",
        "--onedir",
        "--clean",
        "--noconfirm",
        "--collect-all", "playwright",
        "--add-data", "config.example.json;.",
        "--add-data", "content_prompts.json;.",
        "--add-data", "run_debug_chrome.bat;.",
        str(web_app_py)
    ]
    
    # Run pyinstaller
    res = subprocess.run(cmd, shell=False, cwd=str(root))
    
    if res.returncode == 0:
        print("\n=== DONG GOI EXE THANH CONG! ===")
        dist_dir = root / "dist" / "PixelDriveCapture"
        print(f"Thu muc ung dung hoan thien nam tai: {dist_dir}")
        print("Huong dan trien khai:")
        print("1. Copy ca thu muc 'PixelDriveCapture' sang may tinh khac.")
        print("2. Chay file 'PixelDriveCapture.exe' de khoi dong ung dung.")
        print("3. File cau hinh 'config.json' se duoc tu dong tao ra tai do de ban cau hinh IP/Drive.")
    else:
        print("\n=== DONG GOI THAT BAI! ===")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
