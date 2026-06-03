# Pixel Drive Capture & AI Poster Generator / Content Helper

Ứng dụng Web cục bộ (Local Web App) tích hợp đa năng: Điều khiển điện thoại Google Pixel chụp ảnh sản phẩm, tự động đồng bộ Google Drive, **tách nền ghép ảnh sản phẩm lai (Hybrid Composition)** vẽ poster quảng cáo AI chuyên nghiệp, và công cụ **Content Helper tự động hóa ChatGPT** để sinh ảnh bối cảnh miễn phí.

Giao diện ứng dụng được thiết kế theo phong cách Premium Glassmorphism (hỗ trợ Dark/Light Mode), tối ưu hóa 100% quy trình làm việc từ khâu chụp sản phẩm thô đến tạo ra ảnh truyền thông chất lượng cao hoàn thiện.

---

## ✨ Tính Năng Nổi Bật

### 1. Điều Khiển Pixel & Đồng Bộ Drive Tự Động
- **Kết nối linh hoạt**: Điều khiển Pixel chụp ảnh/quay phim thông qua cáp USB hoặc Wi-Fi không dây. Tự động sửa lỗi kết nối offline bằng cơ chế Reconnect.
- **Trình chiếu scrcpy**: Xem trước góc máy và lấy nét trực tiếp từ màn hình máy tính.
- **Đồng bộ bảo mật và chịu lỗi**: Tự động đưa ảnh chụp vào đúng thư mục sản phẩm được chọn trên Google Drive for Desktop. Áp dụng quy trình kiểm tra dung lượng byte nghiêm ngặt trước khi xóa ảnh gốc trên điện thoại để giải phóng dung lượng.
- **Tự động chuyển đổi thông minh (Fallback)**: Tự động chuyển qua lại giữa USB và Wifi nếu một trong hai kết nối bị gián đoạn, tự động mở cổng 5555 qua USB để chạy Wifi.

### 2. Tạo Poster AI Với Sản Phẩm Thật (Hybrid Composition)
- **Bảo toàn sản phẩm thật 100%**: Sử dụng thư viện `rembg` cục bộ để tách nền sản phẩm thực tế, tự ghép đè sản phẩm lên bối cảnh được AI vẽ ra bằng PIL.
- **Vẽ bóng đổ tự nhiên**: Tự động vẽ bóng đổ đen mờ semi-transparent và làm mịn bóng bằng Gaussian Blur dưới chân sản phẩm giúp ảnh ghép hòa hợp 100% với ánh sáng bối cảnh.
- **Tối ưu chi phí & Tốc độ**: Sử dụng mô hình `gpt-image-1-mini` với chất lượng `quality="medium"` giúp tối ưu hóa chi phí API OpenAI ở mức thấp nhất, tạo nhiều ảnh song song chỉ mất 10-15 giây thông qua xử lý bất đồng bộ ThreadPool.
- **Tự động hóa prompt**: GPT-4o Vision tự động phân tích màu sắc, nhãn hiệu sản phẩm và viết lại prompt tiếng Anh tối ưu nhất cho mô hình sinh ảnh vẽ nền.

### 3. Công Cụ Content Helper (Bán Tự Động Qua ChatGPT Web)
- **Tiết kiệm chi phí**: Kết nối trực tiếp vào tab ChatGPT đang mở trên trình duyệt Chrome thật của bạn để ra lệnh tạo ảnh miễn phí.
- **Tự động hóa Playwright**: Tự động click focus, upload ảnh thô, điền prompt mẫu và gửi tin nhắn (giả lập click nút gửi hoặc gõ phím Enter bằng keyboard thật, tương thích React state).
- **Tải ảnh DALL-E thông minh**: Tự động tải ảnh kết quả bằng cơ chế `fetch` nội bộ origin để tránh lỗi bảo mật CORS Tainted Canvas, lưu tệp cục bộ và hiển thị ở cột Ảnh kết quả.
- **Thao tác kéo thả siêu tốc**: Tích hợp nút **"Mở thư mục"** tự động kích hoạt Windows Explorer và bôi đen sẵn (highlight) tệp ảnh vừa tải về để bạn kéo thả trực tiếp vào Photoshop hoặc Canva Web.
- **Thư viện Prompt & Danh mục động**: Quản lý prompts mẫu theo danh mục động (Shopee, Facebook, TikTok Shop...). Giao diện quản lý danh mục (Thêm/Sửa/Xóa) trực quan, tự động đồng bộ danh mục của prompt cũ khi danh mục bị đổi tên hoặc xóa.

---

## 💻 Yêu Cầu Hệ Thống

- **Hệ điều hành**: Windows 10 / 11.
- **Môi trường**: Python 3.11 trở lên.
- **Công cụ đi kèm**:
  - Google Drive for Desktop (đã đăng nhập tài khoản).
  - Android SDK Platform Tools (đã thêm lệnh `adb` vào PATH).
  - [scrcpy](https://github.com/Genymobile/scrcpy) (để chiếu màn hình).
  - Trình duyệt Google Chrome (đã đăng nhập tài khoản ChatGPT).

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
   * Bật **Tùy chọn nhà phát triển** và kích hoạt **Gỡ lỗi USB** trên Pixel.
   * Cắm cáp USB vào máy tính và xác nhận tin cậy thiết bị.

---

## ⚙️ Hướng Dẫn Vận Hành

### 1. Khởi chạy ứng dụng Web
Chạy lệnh để khởi chạy máy chủ Flask:
```powershell
python .\web_app.py
```
Mở trình duyệt và truy cập: **`http://127.0.0.1:8765`** (hoặc tên miền nội bộ `http://pixel-drive-capture:8765`).

### 2. Sử dụng tính năng Content Helper (ChatGPT Web)
1. Hãy tắt hoàn toàn các cửa sổ Chrome bình thường đang mở trên máy.
2. Bấm nút **"Khởi động Chrome"** trên giao diện Content Helper (hoặc chạy tệp `run_debug_chrome.bat`) để mở cửa sổ Chrome debug biệt lập.
3. Trên cửa sổ Chrome mới mở, truy cập `https://chatgpt.com` và đăng nhập tài khoản ChatGPT của bạn ở lần đầu tiên (các lần sau cookie sẽ tự động được lưu).
4. Quay lại giao diện Web Helper, bấm **"Gửi Lên ChatGPT"** để bắt đầu quy trình tự động hóa.

---

## 🛠️ Cấu Hướng Hệ Thống (`config.json`)

Mẫu cấu hình cơ bản (các thông tin nhạy cảm đã được bỏ qua qua `.gitignore`):

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
  },
  "openai": {
    "api_key": "sk-...",
    "export_dir": "C:\\Users\\datdt\\Downloads"
  },
  "content_categories": ["Shopee", "Facebook", "General"]
}
```

---

## 🔒 Quy Trình Bảo Vệ Tệp Tin (Chống Mất File)

Nhằm đảm bảo an toàn tuyệt đối cho dữ liệu ảnh và video sản phẩm, ứng dụng áp dụng quy trình xử lý 6 bước nghiêm ngặt:
1. **Định vị thời gian**: Ghi nhận mốc thời gian bắt đầu thao tác chụp/quay.
2. **Kéo tệp tạm**: Sao chép tệp tin mới nhất từ điện thoại vào thư mục tạm `inbox` trên máy tính.
3. **Đồng bộ Drive**: Chép tệp tin sang thư mục Google Drive đích dưới định dạng tệp tạm thời `.part`.
4. **Xác minh dung lượng**: So sánh dung lượng byte của tệp tin đích và tệp tin gốc để đảm bảo quá trình đồng bộ hoàn tất 100%.
5. **Chốt tệp**: Đổi tên tệp tin tạm `.part` thành tên chính thức trên Google Drive.
6. **Giải phóng bộ nhớ**: Xóa tệp tin gốc trên điện thoại Pixel và tệp tạm trong thư mục `inbox`.

---

## 🛡️ Bảo Mật & Riêng Tư

Các tệp cấu hình chứa API key, token hoặc thông tin cá nhân được bỏ qua hoàn toàn thông qua `.gitignore` và không bao giờ được đẩy lên kho chứa công cộng:
- `.env`
- `config.json`
- `client_secret.json` / `token.json`
- Các thư mục dữ liệu cục bộ (`inbox/`, `processed/`, `logs/`)
