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
- **Thư viện Prompt & Danh mục động**: Quản lý prompts mẫu theo danh mục động (Shopee, Facebook, TikTok Shop...). Giao diện quản lý danh mục (Thêm/Sửa/Xóa) trực quan, tự động đồng bộ danh mục và hỗ trợ **nhập (import) hàng loạt prompt từ file `.txt`** siêu tốc.

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

### 3. Vận hành thông qua File EXE Đóng Gói (Windows)
Ứng dụng hỗ trợ đóng gói hoàn chỉnh sang thư mục chạy độc lập (không cần cài Python ở máy đích):
1. **Biên dịch**: Tại thư mục dự án, chạy lệnh:
   ```powershell
   python .\build_exe.py
   ```
2. **Triển khai**: Copy thư mục `dist/PixelDriveCapture` sang máy tính khác.
3. **Khởi chạy**: Click đúp tệp **`PixelDriveCapture.exe`** để chạy trực tiếp Flask server. Các file cấu hình (`config.json`, `content_prompts.json`, `run_debug_chrome.bat`) sẽ tự động được sinh ra ở ngoài thư mục root để bạn dễ dàng chỉnh sửa cấu hình.

---

## 📤 Hướng Dẫn Nhập (Import) Prompt Mẫu Hàng Loạt

Tính năng **"+ Nhập file"** cho phép bạn import hàng loạt prompt từ một tệp `.txt` vào thư viện. 

### 1. Cú pháp tệp tin `.txt` mẫu
Mỗi prompt được ngăn cách bằng dòng chứa ba dấu gạch ngang `---` hoặc dấu bằng `===`. Cấu trúc cụ thể bao gồm các từ khóa `Danh mục:`, `Tiêu đề:`, và `Nội dung:` như sau:

```text
Danh mục: Shopee
Tiêu đề: Bối cảnh Studio Xanh Lá
Nội dung: Vui lòng vẽ một bối cảnh studio quảng cáo cao cấp cho sản phẩm trong ảnh này. Đặt sản phẩm trên bệ đá cẩm thạch trắng, xung quanh là các lá cây nhiệt đới màu xanh mướt...
---
Danh mục: Facebook
Tiêu đề: Bối cảnh bãi cát mùa hè
Nội dung: Vui lòng vẽ một bối cảnh mùa hè năng động cho sản phẩm này. Đặt sản phẩm trên bãi cát mịn màu vàng nhạt, có sóng biển xanh trong...
---
Danh mục: Tiktok Shop
Tiêu đề: Bối cảnh Livestream Đỏ Rực
Nội dung: Vẽ một bối cảnh sân khấu livestream đỏ rực rỡ, ánh đèn LED rực rỡ chiếu sáng...
Nội dung có thể xuống dòng viết tiếp ở đây thoải mái
```

> [!NOTE]
> * **Tự đăng ký danh mục**: Nếu tên danh mục trong file import chưa có trong hệ thống (ví dụ: `Tiktok Shop`), hệ thống sẽ **tự động thêm danh mục** này vào file cấu hình `config.json` và hiển thị trên giao diện lọc.
> * **Xử lý nội dung nhiều dòng**: Toàn bộ văn bản bên dưới dòng `Nội dung:` sẽ được gom đầy đủ (bao gồm cả các ký tự xuống dòng) cho tới khi gặp prompt tiếp theo.

### 2. Các bước thực hiện
1. Trên giao diện Web app, nhìn vào panel **Thư viện Prompt** (cột 1) -> Chọn nút **`+ Nhập file`** (màu xanh lá).
2. Chọn tệp tin `.txt` chứa danh sách prompt của bạn.
3. Nhật ký hệ thống sẽ thông báo số lượng prompt đã import thành công, giao diện Thư viện Prompt và bộ lọc sẽ tự động làm mới để cập nhật dữ liệu.

## 🔄 Tự Động Cập Nhật Phần Mềm (Auto-Update)

Ứng dụng hỗ trợ kiểm tra và cập nhật tự động trực tiếp từ GitHub Releases:

1. **Hiển thị phiên bản**: Phiên bản hiện tại của phần mềm được hiển thị trên nút ở góc trên bên phải (ví dụ: `v1.1.0`).
2. **Kiểm tra tự động**: Mỗi khi mở ứng dụng, phần mềm sẽ tự động kiểm tra ngầm phiên bản mới trên GitHub Releases. Nếu phát hiện có phiên bản mới hơn trên GitHub, nút phiên bản sẽ tự động đổi màu và **nhấp nháy nhịp thở (`pulse-warn`)** để báo hiệu cho bạn.
3. **Quy trình cập nhật cài đè an toàn**: 
   - Khi click vào nút phiên bản, một hộp thoại thông tin bản cập nhật mới sẽ hiển thị.
   - Nếu bạn chọn đồng ý, ứng dụng sẽ tải tệp tin cập nhật dạng `.zip` từ GitHub Releases về thư mục tạm, tự động giải nén và kích hoạt một tiến trình updater chạy độc lập.
   - Ứng dụng cũ sẽ tự tắt để giải phóng khóa tệp, tiến trình updater sẽ ghi đè toàn bộ các file mới vào thư mục hiện tại (ngoại trừ tệp `config.json` và `config.example.json` để **giữ lại nguyên vẹn cấu hình của bạn**), sau đó tự khởi động lại phiên bản mới và dọn dẹp các tệp tạm.

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
