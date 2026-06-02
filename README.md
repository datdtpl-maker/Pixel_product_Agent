# Pixel Drive Capture

Ứng dụng Web cục bộ (Local Web App) điều khiển điện thoại Google Pixel chụp ảnh/quay phim sản phẩm và tự động đồng bộ hóa trực tiếp vào thư mục Google Drive (thông qua Google Drive for Desktop) trên Windows. 

Giao diện ứng dụng được thiết kế hiện đại (Sleek Glassmorphism Dark/Light Mode), giúp tối ưu hóa quy trình làm việc cho nhân viên studio chụp ảnh sản phẩm một cách nhanh chóng và an toàn.

---

## ✨ Tính Năng Nổi Bật

- **Điều khiển Pixel linh hoạt**: Kết nối và điều khiển Pixel thông qua cáp USB hoặc mạng Wi-Fi không dây nội bộ.
- **Xem trước thời gian thực (Preview)**: Tích hợp trình chiếu màn hình Pixel qua `scrcpy` để căn góc máy và lấy nét trực tiếp từ máy tính.
- **Đồng bộ Google Drive an toàn**: Tự động chuyển tệp tin ảnh/video vào đúng thư mục sản phẩm được lựa chọn trên Google Drive for Desktop.
- **Cơ chế chống mất file**: Xác minh tính toàn vẹn của tệp tin trước khi tiến hành xóa file gốc trên điện thoại để giải phóng bộ nhớ.
- **Giao diện hiện đại**: Hỗ trợ chuyển đổi chủ động giao diện Sáng/Tối (Light/Dark Mode).

---

## 💻 Yêu Cầu Hệ Thống

- **Hệ điều hành**: Windows 10 / 11.
- **Môi trường**: Python 3.11 trở lên.
- **Công cụ đi kèm**:
  - Google Drive for Desktop (đã đăng nhập tài khoản đồng bộ).
  - Android SDK Platform Tools (đã thêm lệnh `adb` vào PATH).
  - [scrcpy](https://github.com/Genymobile/scrcpy) (để trình chiếu màn hình).

---

## 🚀 Hướng Dẫn Cài Đặt Nhanh

1. **Tải mã nguồn và cài đặt thư viện**:
   ```powershell
   git clone https://github.com/datdtpl-maker/Pixel-Drive-Capture.git
   cd Pixel-Drive-Capture
   python -m pip install -r requirements.txt
   ```

2. **Khởi tạo tệp cấu hình**:
   ```powershell
   Copy-Item config.example.json config.json
   ```

3. **Thiết lập điện thoại Pixel**:
   * Kích hoạt **Tùy chọn nhà phát triển** và bật **Gỡ lỗi USB** trên Pixel.
   * Cắm cáp USB vào máy tính và xác nhận tin cậy thiết bị.

---

## 🛠️ Cấu Hình Cục Bộ (`config.json`)

Mẫu cấu hình cơ bản (không chứa thông tin cá nhân):

```json
{
  "paths": {
    "inbox_dir": "inbox",
    "processed_dir": "processed",
    "drive_root_dir": "G:\\My Drive\\Ten_Thu_Muc_Chinh",
    "selected_drive_folder": ""
  },
  "pixel": {
    "adb_serial": "",
    "camera_dir": "/sdcard/DCIM/Camera",
    "connection_mode": "usb",
    "wifi_ip": ""
  }
}
```

*Nếu bạn có nhiều thiết bị Android cắm vào máy tính, hãy điền mã serial của Pixel vào mục `adb_serial` để định tuyến chính xác.*

---

## ⚙️ Hướng Dẫn Vận Hành

### 1. Khởi chạy ứng dụng Web
Chạy lệnh khởi chạy máy chủ:
```powershell
python .\web_app.py
```
Mở trình duyệt và truy cập: **`http://127.0.0.1:8765`**

*(Tùy chọn) Để đăng ký và sử dụng tên miền nội bộ `http://pixel-drive-capture:8765`, hãy chạy PowerShell bằng quyền Administrator và thực thi:*
```powershell
powershell -ExecutionPolicy Bypass -File .\add_internal_domain.ps1
```

### 2. Tự động khởi chạy cùng Windows
* Cài đặt Shortcut vào thư mục Startup:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\install_startup_shortcut.ps1
  ```
* Gỡ bỏ cài đặt tự khởi động:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\uninstall_startup_shortcut.ps1
  ```

---

## 🔒 Cơ Chế Bảo Vệ Tệp Tin (Chống Mất File)

Nhằm đảm bảo an toàn tuyệt đối cho dữ liệu ảnh và video sản phẩm, ứng dụng áp dụng quy trình xử lý 6 bước nghiêm ngặt:
1. **Định vị thời gian**: Ghi nhận mốc thời gian bắt đầu thao tác chụp/quay.
2. **Kéo tệp tạm**: Tìm kiếm và sao chép tệp tin mới nhất từ điện thoại vào thư mục tạm `inbox` trên máy tính.
3. **Đồng bộ Drive**: Chép tệp tin sang thư mục Google Drive đích dưới định dạng tệp tạm thời `.part`.
4. **Xác minh dung lượng**: So sánh dung lượng byte của tệp tin đích và tệp tin gốc để đảm bảo quá trình đồng bộ hoàn tất 100%.
5. **Chốt tệp**: Đổi tên tệp tin tạm `.part` thành tên chính thức trên Google Drive.
6. **Giải phóng bộ nhớ**: Xóa tệp tin gốc trên điện thoại Pixel và tệp tạm trong thư mục `inbox`.

*Nếu xảy ra bất kỳ lỗi kết nối Drive nào ở bước trung gian, tệp gốc trên Pixel luôn được giữ nguyên.*

---

## 🛡️ Bảo Mật & Riêng Tư

Các tệp cấu hình chứa API key, token hoặc thông tin cá nhân được bỏ qua hoàn toàn thông qua `.gitignore` và không bao giờ được đẩy lên kho chứa công cộng:
- `.env`
- `config.json`
- `client_secret.json` / `token.json`
- Các thư mục log và dữ liệu chạy cục bộ (`inbox/`, `processed/`, `logs/`)
