# Pixel Product Agent

Pixel Product Agent là ứng dụng local dùng để điều khiển điện thoại Google Pixel chụp ảnh/quay video sản phẩm, nhận diện sản phẩm bằng AI, tự tạo album Google Photos theo tên sản phẩm và upload media vào đúng album.

Ứng dụng chạy trên Windows, điều khiển Pixel qua ADB, xem trước màn hình bằng scrcpy và cung cấp giao diện web local để thao tác thay vì gõ lệnh thủ công.

## Tính năng chính

- Chụp ảnh từ Google Pixel và upload Google Photos bằng một nút bấm.
- Quay video từ Google Pixel và upload vào album sản phẩm.
- Xem trước màn hình/camera Pixel bằng scrcpy để chỉnh góc chụp trước khi bấm chụp.
- Nhận diện sản phẩm bằng OpenAI, Gemini hoặc cả hai cùng lúc.
- Nạp catalog sản phẩm từ thư mục dữ liệu gồm ảnh mẫu, barcode và tài liệu `.txt`, `.csv`, `.json`, `.docx`, `.pdf`.
- Tự tìm thêm dữ liệu sản phẩm trên internet bằng SerpAPI hoặc Bing Image Search khi catalog chưa đủ.
- Tự tạo album Google Photos theo tên sản phẩm.
- Tái sử dụng album đã có nếu tên sản phẩm gần giống nhau, ví dụ tiếng Việt và tiếng Anh của cùng một sản phẩm.
- Log tiến trình realtime trên giao diện: chụp, kéo file, AI phân loại, tạo album, upload.
- Có script khởi động cùng Windows.

## Yêu cầu hệ thống

- Windows 10/11.
- Python 3.11 trở lên.
- Google Pixel hoặc điện thoại Android có bật USB debugging.
- ADB đã cài và gọi được bằng lệnh `adb`.
- scrcpy để xem màn hình Pixel.
- Tài khoản Google Cloud có OAuth Desktop app cho Google Photos Library API.
- Ít nhất một AI key: OpenAI hoặc Gemini.
- Tùy chọn: SerpAPI hoặc Bing Image Search nếu muốn agent tìm hình sản phẩm trên internet.

## Cài đặt nhanh

Clone source:

```powershell
git clone https://github.com/datdtpl-maker/hermes-agent-photo-google.git
cd hermes-agent-photo-google
```

Cài thư viện Python:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Tạo file cấu hình local:

```powershell
Copy-Item config.example.json config.json
```

Các file sau là file riêng tư, không commit lên Git:

```text
.env
client_secret.json
token.json
config.json
album_cache.json
```

## Cài ADB và kết nối Pixel

1. Trên Pixel, bật **Developer options**.
2. Bật **USB debugging**.
3. Cắm Pixel vào máy tính bằng USB.
4. Chấp nhận RSA debugging prompt trên điện thoại.
5. Kiểm tra:

```powershell
adb devices
```

Kết quả hợp lệ có dạng:

```text
List of devices attached
23241JEGR00378    device
```

Nếu có nhiều thiết bị, điền serial vào `config.json`:

```json
"pixel": {
  "adb_serial": "23241JEGR00378",
  "camera_dir": "/sdcard/DCIM/Camera"
}
```

## Cài scrcpy để xem trước màn hình

Ứng dụng sẽ tự tìm `scrcpy` theo thứ tự:

1. Biến môi trường `SCRCPY_PATH`.
2. Đường dẫn mặc định:

```text
C:\FastbootFirmwareFlasher\ExtraTools\scrcpy\scrcpy.exe
```

3. Lệnh `scrcpy` trong `PATH`.

Nếu scrcpy ở chỗ khác, thêm vào `.env`:

```text
SCRCPY_PATH=C:\path\to\scrcpy.exe
```

Trên giao diện web, bấm **Xem màn hình Pixel** để mở camera trên Pixel và xem live preview trước khi chụp.

## Cấu hình Google Photos OAuth

1. Vào Google Cloud Console.
2. Tạo hoặc chọn project.
3. Enable **Google Photos Library API**.
4. Vào OAuth consent screen:
   - User type: `External` cho app cá nhân/test.
   - Thêm Gmail dùng Google Photos vào test users nếu app còn ở testing mode.
5. Tạo OAuth client:
   - Type: `OAuth client ID`.
   - Application type: `Desktop app`.
6. Download JSON và lưu vào thư mục project với tên:

```text
client_secret.json
```

Đăng nhập lần đầu:

```powershell
python .\photo_pipeline.py auth
```

Trình duyệt sẽ mở ra để đăng nhập Google. Sau khi xác thực xong, app tạo `token.json` để dùng cho các lần upload sau.

Ghi chú quan trọng: Google Photos API với scope `photoslibrary.appendonly` chỉ upload media và thêm vào album do app tạo/quản lý. Giữ `album_cache.json` để app nhớ album ID và tránh tạo trùng album.

## Cấu hình AI key

Cách dễ nhất là nhập key trên giao diện web tại mục **Cấu hình API AI** rồi bấm **Lưu server**.

Hoặc tạo `.env` thủ công:

```text
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
```

Provider hỗ trợ:

- `OpenAI`
- `Gemini`
- `OpenAI + Gemini`
- `Offline mẫu ảnh`

Chế độ khuyến nghị là `OpenAI + Gemini`. Nếu một provider lỗi, provider còn lại vẫn có thể trả kết quả.

## Cấu hình tìm sản phẩm trên internet

Khi catalog không nhận ra sản phẩm, agent có thể dùng AI đọc ảnh, tạo truy vấn tìm kiếm, lấy kết quả hình ảnh web và quyết định tên sản phẩm nếu đủ tin cậy.

Provider hỗ trợ:

- `SerpAPI Google Images`
- `Bing Image Search`

Google Custom Search đã bị loại khỏi app vì Google Custom Search JSON API không còn phù hợp cho nhiều project/key mới.

Biến `.env` tương ứng:

```text
SERPAPI_API_KEY=...
BING_SEARCH_API_KEY=...
```

Trên giao diện web:

1. Chọn Search provider.
2. Nhập Search API key.
3. Chọn ngưỡng tự tạo album, ví dụ `0.78`.
4. Bấm **Lưu cấu hình tìm web**.
5. Bấm **Kiểm tra Search API**.

## Chuẩn bị dữ liệu sản phẩm

Khuyến nghị mỗi sản phẩm là một thư mục riêng:

```text
D:\product-data
|-- Eskar Tears Artificial Tears 15ml
|   |-- front.jpg
|   |-- back.jpg
|   |-- barcode.jpg
|-- Thuoc Paracetamol PV Pharma
|   |-- front.jpg
|   |-- label.jpg
|-- danh-sach-san-pham.txt
```

File tài liệu có thể chứa tên sản phẩm, SKU, barcode hoặc mô tả. Định dạng được hỗ trợ:

```text
.txt
.csv
.json
.docx
.pdf
```

Ảnh mẫu nên gồm:

- mặt trước sản phẩm;
- mặt sau/nhãn phụ nếu có;
- barcode/SKU nếu rõ;
- 2-5 ảnh mỗi sản phẩm nếu các sản phẩm nhìn giống nhau.

## Chạy giao diện web

Chạy server:

```powershell
python .\web_app.py
```

Mở trình duyệt:

```text
http://127.0.0.1:8765
```

Nếu muốn dùng tên miền nội bộ:

```powershell
# Mở PowerShell bằng Run as Administrator
.\add_internal_domain.ps1
```

Sau đó mở:

```text
http://pixel-agent.test:8765
```

## Quy trình sử dụng hằng ngày

1. Cắm Pixel vào máy tính.
2. Mở app web.
3. Kiểm tra trạng thái Pixel ADB, Google token, AI key.
4. Bấm **Xem màn hình Pixel** để mở live preview.
5. Chỉnh góc sản phẩm trên camera.
6. Bấm **Chụp ảnh từ Pixel và upload** hoặc **Quay video từ Pixel và upload**.
7. Theo dõi tiến trình trong **Nhật ký xử lý**.
8. Kiểm tra Google Photos album.

Nếu muốn ép tên sản phẩm khi test, nhập tên vào ô **Ép tên sản phẩm khi test**. Khi dùng thật, để trống để AI tự nhận diện.

## Chạy cùng Windows

Tạo shortcut khởi động cùng Windows:

```powershell
.\install_startup_shortcut.ps1
```

Gỡ shortcut:

```powershell
.\uninstall_startup_shortcut.ps1
```

Chạy thủ công bằng launcher:

```powershell
.\start_pixel_agent.ps1
```

Ứng dụng dùng port `8765`, không trùng với app khác đang chạy port `3210`.

Lưu ý: các script startup hiện chứa đường dẫn project local. Nếu clone repo sang máy/thư mục khác, chỉnh lại biến `$ProjectDir` trong các file `.ps1`.

## Lệnh CLI hữu ích

Chụp ảnh từ Pixel, phân loại và upload:

```powershell
python .\photo_pipeline.py run-once
```

Chụp ảnh và ép tên album:

```powershell
python .\photo_pipeline.py run-once --product "Tên sản phẩm"
```

Quay video 10 giây, phân loại bằng ảnh tham chiếu và upload:

```powershell
python .\photo_pipeline.py record-once --duration 10
```

Upload ảnh có sẵn:

```powershell
python .\photo_pipeline.py upload .\inbox\test.jpg --product "Tên sản phẩm"
```

Chỉ test nhận diện, không upload:

```powershell
python .\photo_pipeline.py classify .\inbox\test.jpg
```

Chạy lặp lại:

```powershell
python .\photo_pipeline.py watch --interval 30 --count 5
```

## Xử lý lỗi thường gặp

`adb devices` không thấy Pixel:

- kiểm tra cáp USB;
- bật USB debugging;
- approve RSA prompt trên điện thoại;
- chạy lại `adb kill-server` rồi `adb start-server`.

Không mở được scrcpy:

- kiểm tra `SCRCPY_PATH`;
- chạy thử trực tiếp `scrcpy.exe`;
- đảm bảo ADB thấy Pixel.

App upload nhầm ảnh cũ:

- bản mới đã chặn bằng timestamp, chỉ nhận file tạo sau thời điểm bấm chụp/quay;
- nếu camera không tạo ảnh mới, app sẽ báo lỗi thay vì upload ảnh cũ.

Tạo trùng album:

- app dùng `album_cache.json` để nhớ album;
- bản mới có so tên gần giống để gom tên tiếng Việt/tiếng Anh về cùng album;
- album đã lỡ tạo trùng trên Google Photos cần xóa thủ công.

Google token hết hạn hoặc revoke:

```powershell
Remove-Item .\token.json
python .\photo_pipeline.py auth
```

## Bảo mật

- Không commit `.env`, `client_secret.json`, `token.json`, `config.json`, `album_cache.json`.
- Không gửi API key trong chat hoặc ticket.
- Nếu key đã lộ, rotate hoặc tạo key mới.
- Với triển khai nhiều người dùng, cần backend riêng, đăng nhập người dùng, phân quyền thiết bị, mã hóa token và audit log.

## Ghi chú production

Repo này là local edge-agent prototype. Để phục vụ hàng ngàn người dùng, nên tách kiến trúc:

- worker local điều khiển Pixel/ADB/scrcpy;
- backend quản lý user, thiết bị, catalog và job queue;
- database thay cho JSON local;
- storage và audit log tập trung;
- cơ chế retry, quota tracking và monitoring;
- OAuth token lưu mã hóa theo từng user.
