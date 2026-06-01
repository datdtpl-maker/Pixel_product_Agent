# Huong Dan Trien Khai Pixel Drive Capture Tren May Moi

Tai lieu nay dung khi copy tool sang mot may Windows khac de dieu khien Pixel chup anh/quay video va ghi file vao Google Drive for desktop.

## 1. File can copy

Copy toan bo thu muc package `pixel-drive-capture-package` sang may moi. Package nay chi gom file runtime can thiet:

- `web_app.py`
- `photo_pipeline.py`
- `requirements.txt`
- `config.example.json`
- `README.md`
- `DEPLOY_NEW_MACHINE.md`
- `start_pixel_agent.ps1`
- `run_pixel_test.ps1`
- `add_internal_domain.ps1`
- `install_startup_shortcut.ps1`
- `install_startup_task.ps1`
- `uninstall_startup_shortcut.ps1`
- `uninstall_startup_task.ps1`

Khong copy cac file rieng tu hoac file cua may cu:

- `.env`
- `config.json`
- `client_secret.json`
- `token.json`
- `album_cache.json`
- `inbox/`
- `processed/`
- `logs/`
- `__pycache__/`
- `.git/`

## 2. Phan mem can cai tren may moi

1. Cai Python 3.11 tro len.
   - Khi cai, bat tuy chon `Add python.exe to PATH`.
   - Kiem tra:

```powershell
python --version
```

2. Cai Google Drive for desktop va dang nhap tai khoan can dong bo.
   - Tao thu muc goc de luu san pham, vi du:

```text
G:\My Drive\Test hinh anh shopee
```

3. Cai Android Platform Tools de co lenh `adb`.
   - Kiem tra:

```powershell
adb version
adb devices
```

4. Cai `scrcpy` de xem man hinh Pixel.
   - Dat `scrcpy.exe` vao PATH, hoac tao file `.env` trong thu muc tool:

```text
SCRCPY_PATH=C:\path\to\scrcpy.exe
```

## 3. Chuan bi Pixel

1. Bat Developer options.
2. Bat USB debugging.
3. Cam cap USB vao may moi.
4. Tren dien thoai, chap nhan hop thoai Allow USB debugging.
5. Kiem tra:

```powershell
adb devices
```

Ket qua hop le phai co trang thai `device`, vi du:

```text
23241JEGR00378    device
```

### Ket noi Pixel qua Wifi (Khong day)

Neu muon ket noi khong day qua Wifi:
1. Cam cap USB vao may tinh 1 lan duy nhat de kich hoat.
2. Chạy file script ket noi tu dong trong PowerShell:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\connect_pixel_wifi.ps1
   ```
3. Script se tu dong lay IP cua Pixel, kich hoat che do TCP/IP 5555 va ket noi khong day.
4. Khi script thong bao thanh cong, ban co the **RUT CAP USB** ra va su dung tool hoan toan khong day!

## 4. Cai tool tren may moi

Mo PowerShell trong thu muc tool da copy:

```powershell
cd "C:\duong-dan\pixel-drive-capture"
python -m pip install -r requirements.txt
Copy-Item .\config.example.json .\config.json
```

Neu may moi co nhieu thiet bi Android, mo `config.json` va dien `adb_serial`:

```json
"pixel": {
  "adb_serial": "SERIAL_CUA_PIXEL",
  "camera_dir": "/sdcard/DCIM/Camera"
}
```

Neu Google Drive tren may moi khong nam o `G:\My Drive\Test hinh anh shopee`, co the sua tren giao dien web sau khi chay app, hoac sua truoc trong `config.json`:

```json
"drive_root_dir": "D:\\Google Drive\\Ten thu muc san pham"
```

## 5. Chay thu

```powershell
python .\web_app.py
```

Mo trinh duyet:

```text
http://127.0.0.1:8765
```

Kiem tra tren giao dien:

- Pixel ADB phai hien serial thiet bi.
- Thu muc Drive phai hien `Da ket noi`.
- Tao hoac chon thu muc san pham.
- Bam `Xem man hinh Pixel` de mo scrcpy.
- Bam `Chup anh` hoac `Quay video`.
- Bam `Bat / tat man hinh Pixel` khi can khoa hoac danh thuc man hinh. Khi tat, nut nay dong scrcpy va dua Pixel ve che do sleep.

## 6. Tao ten mien noi bo

Mo PowerShell bang quyen Administrator:

```powershell
cd "C:\duong-dan\pixel-drive-capture"
powershell -ExecutionPolicy Bypass -File .\add_internal_domain.ps1
```

Sau do mo:

```text
http://pixel-drive-capture:8765
```

## 7. Cho app tu chay khi bat may

Cach de dung nhat la shortcut Startup:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_startup_shortcut.ps1
```

Neu muon dung Windows Task Scheduler:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_startup_task.ps1
```

## 8. Kiem tra loi nhanh

Neu khong thay Pixel:

```powershell
adb kill-server
adb start-server
adb devices
```

Neu khong mo duoc scrcpy:

- Kiem tra `scrcpy.exe` co nam trong PATH khong.
- Hoac tao `.env` co `SCRCPY_PATH=...`.

Neu Drive bao loi:

- Kiem tra Google Drive for desktop da dang nhap.
- Kiem tra duong dan thu muc goc co ton tai.
- Tao thu muc san pham truoc khi chup/quay.

Neu app khong mo duoc cong 8765:

- Kiem tra co app khac dang dung port 8765 khong.
- Co the doi port khi chay:

```powershell
$env:PORT="8766"
python .\web_app.py
```
