# Pixel Drive Capture

Pixel Drive Capture là ứng dụng web local dùng để điều khiển điện thoại Google Pixel chụp ảnh hoặc quay video sản phẩm và lưu trực tiếp vào thư mục Google Drive for desktop trên Windows.

Luồng web hiện tại không dùng AI phân loại, không tạo album Google Photos và không cần OAuth Google Photos. Nhân viên chủ động tạo hoặc chọn đúng thư mục sản phẩm trước khi chụp. Sau khi file đã được chép và kiểm tra thành công trong Google Drive đồng bộ, app mới xóa file gốc khỏi Pixel.

## Quy trình vận hành

1. Mở giao diện web.
2. Kiểm tra trạng thái Pixel ADB và thư mục Drive.
3. Tạo thư mục sản phẩm mới hoặc chọn thư mục đã có.
4. Bấm **Xem màn hình Pixel** để chỉnh góc máy bằng scrcpy.
5. Bấm **Chụp ảnh** hoặc **Quay video**.
6. Theo dõi log: kéo file từ Pixel, chép file vào Drive, xác minh dung lượng và xóa file khỏi Pixel.

Thư mục Drive mặc định:

```text
G:\My Drive\Test hình ảnh shopee
```

Có thể đổi đường dẫn này trực tiếp trên giao diện web.

## Yêu cầu

- Windows 10 hoặc Windows 11.
- Python 3.11 trở lên.
- Google Drive for desktop đã đăng nhập và đồng bộ ổ `G:`.
- Google Pixel hoặc điện thoại Android có bật USB debugging.
- ADB gọi được bằng lệnh `adb`.
- scrcpy để xem trước màn hình Pixel.

Khuyến nghị: tắt tính năng backup Google Photos trên điện thoại dùng để chụp sản phẩm. App chỉ xóa file local khỏi Pixel; app không xóa ảnh đã backup trên cloud Google Photos.

## Cài đặt

```powershell
git clone https://github.com/datdtpl-maker/Pixel-Drive-Capture.git
cd Pixel-Drive-Capture
python -m pip install -r requirements.txt
Copy-Item config.example.json config.json
```

Kiểm tra kết nối Pixel:

```powershell
adb devices
```

Kết quả hợp lệ:

```text
List of devices attached
23241JEGR00378    device
```

Nếu có nhiều điện thoại, điền serial vào `config.json`:

```json
"pixel": {
  "adb_serial": "23241JEGR00378",
  "camera_dir": "/sdcard/DCIM/Camera"
}
```

## Cấu hình scrcpy

App tìm `scrcpy.exe` theo thứ tự:

1. Biến môi trường `SCRCPY_PATH`.
2. Đường dẫn mặc định:

```text
C:\FastbootFirmwareFlasher\ExtraTools\scrcpy\scrcpy.exe
```

3. Lệnh `scrcpy` trong `PATH`.

Nếu scrcpy nằm ở vị trí khác, tạo file `.env`:

```text
SCRCPY_PATH=C:\path\to\scrcpy.exe
```

## Chạy ứng dụng

```powershell
python .\web_app.py
```

Mở trình duyệt:

```text
http://127.0.0.1:8765
```

## Khởi động cùng Windows

Cài shortcut startup:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_startup_shortcut.ps1
```

Hoặc cài Scheduled Task:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_startup_task.ps1
```

Các script tự nhận diện thư mục cài đặt hiện tại, nên có thể clone repo vào vị trí khác mà không cần sửa đường dẫn thủ công.

Gỡ cài đặt:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_startup_shortcut.ps1
powershell -ExecutionPolicy Bypass -File .\uninstall_startup_task.ps1
```

## Cấu hình Drive

File `config.json` chứa:

```json
"paths": {
  "inbox_dir": "inbox",
  "processed_dir": "processed",
  "drive_root_dir": "G:\\My Drive\\Test hình ảnh shopee",
  "selected_drive_folder": ""
}
```

- `drive_root_dir`: thư mục chính chứa các thư mục sản phẩm.
- `selected_drive_folder`: thư mục sản phẩm đang chọn gần nhất. Giao diện web tự cập nhật giá trị này.
- `inbox_dir`: thư mục tạm local trong quá trình kéo file từ Pixel.

## Cơ chế chống mất file

Khi chụp hoặc quay, app thực hiện theo thứ tự:

1. Ghi nhận thời điểm bắt đầu thao tác.
2. Chỉ lấy file mới được Pixel tạo sau thời điểm đó.
3. Kéo file vào thư mục `inbox`.
4. Chép sang thư mục Drive bằng file tạm `.part`.
5. So sánh dung lượng nguồn và đích.
6. Đổi tên file `.part` thành tên chính thức.
7. Chỉ sau khi xác minh thành công mới xóa file khỏi Pixel và xóa file tạm local.

Nếu Drive lỗi hoặc bị ngắt kết nối, app giữ nguyên file trên Pixel.

App chỉ cho phép một tác vụ chụp hoặc quay chạy tại một thời điểm. Nếu nhiều tab trình duyệt cùng thao tác, yêu cầu đến sau sẽ bị từ chối để tránh trộn file giữa hai lượt.

## File riêng tư

Không commit các file local hoặc khóa API:

```text
.env
config.json
inbox/
processed/
logs/
```
