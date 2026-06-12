import subprocess
import sys
import shutil
import os
from pathlib import Path

def find_or_install_inno_setup():
    """Tim duong dan ISCC.exe cua Inno Setup, hoac tu dong cai dat qua winget neu chua co."""
    # 1. Thu tim trong PATH he thong
    iscc_path = shutil.which("iscc")
    if iscc_path:
        return iscc_path
        
    # 2. Thu kiem tra cac duong dan mac dinh tren Windows
    possible_paths = [
        Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("LOCALAPPDATA", "C:\\Users\\datdt\\AppData\\Local")) / "Programs" / "Inno Setup 6" / "ISCC.exe"
    ]
    for p in possible_paths:
        if p.exists():
            return str(p)
            
    # 3. Neu khong tim thay, tien hanh cai dat tu dong bang winget
    print("Khong tim thay Inno Setup tren may. Dang tien hanh cai dat tu dong qua winget...")
    try:
        # Cai dat Inno Setup o che do silent
        cmd = [
            "winget", "install", "--id", "jrsoftware.InnoSetup",
            "--silent", "--accept-source-agreements", "--accept-package-agreements"
        ]
        res = subprocess.run(cmd, shell=True)
        if res.returncode == 0:
            print("Cai dat Inno Setup thanh cong!")
            # Quet lai cac duong dan mac dinh sau khi cai
            for p in possible_paths:
                if p.exists():
                    return str(p)
        else:
            print(f"Lenh winget cai dat that bai voi ma loi: {res.returncode}")
    except Exception as e:
        print(f"Loi khi goi winget de cai dat Inno Setup: {e}")
        
    return None

def build():
    print("=== BAT DAU TIEN TRINH DONG GOI EXE & SETUP ===")
    
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
    dist_dir = root / "dist" / "MCPShopee"
    
    # Don dep thu muc build cu truoc de tranh loi lock file
    if dist_dir.exists():
        print(f"Dang don dep thu muc cu tai: {dist_dir}...")
        try:
            shutil.rmtree(dist_dir)
        except Exception as e:
            print(f"Canh bao: Khong the xoa hoan toan thu muc dist cu (co the co file dang mo): {e}")
    
    # 3. Chay lenh PyInstaller
    print("Dang chay PyInstaller de dong goi ung dung...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=MCPShopee",
        "--onedir",
        "--clean",
        "--noconfirm",
        "--noconsole",
        "--icon=app_icon.ico",
        "--collect-all", "playwright",
        "--add-data", "config.example.json;.",
        "--add-data", "content_prompts.json;.",
        "--add-data", "run_debug_chrome.bat;.",
        "--add-data", "favicon.ico;.",
        "--add-data", "app_icon.ico;.",
        "--add-data", "shopee_sync;shopee_sync",
        str(web_app_py)
    ]
    
    res = subprocess.run(cmd, shell=False, cwd=str(root))
    
    if res.returncode == 0:
        print("\n=== DONG GOI PYINSTALLER THANH CONG! ===")
        
        # 4. Dong goi thanh bo cai dat Setup (.exe) su dung Inno Setup
        iscc_path = find_or_install_inno_setup()
        if iscc_path:
            print(f"Dang bien dich file Setup bang Inno Setup (Duong dan ISCC: {iscc_path})...")
            iss_file = root / "installer.iss"
            setup_res = subprocess.run([iscc_path, str(iss_file)], shell=False, cwd=str(root))
            if setup_res.returncode == 0:
                print("\n=== TAO BO CAI DAT SETUP THANH CONG! ===")
                print(f"File cai dat cua ban nam tai: {root / 'dist' / 'MCPShopeeSetup.exe'}")
                print("Ban co the gui file nay cho may khac de cai dat truc tiep.")
            else:
                print(f"\n=== LOI: Bien dich Inno Setup that bai! Ma loi: {setup_res.returncode} ===")
        else:
            print("\n=== CANH BAO: Khong tim thay hoac cai dat duoc Inno Setup. Chi co file chay goc trong thu muc dist. ===")
    else:
        print("\n=== DONG GOI PYINSTALLER THAT BAI! ===")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
