# Pixel to Google Photos MVP

This MVP captures or imports product photos, classifies them into a product name, creates a Google Photos album with that product name, and uploads the photo.

Google Photos API note: new uploads can be added to albums created by this script/app. Keep `album_cache.json`; if it is deleted, the script may create duplicate albums with the same title.

## Setup

1. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Copy config:

   ```powershell
   Copy-Item config.example.json config.json
   ```

3. Create Google OAuth credentials:

   - Open Google Cloud Console.
   - Create or choose a project.
   - Enable **Google Photos Library API**.
   - Create OAuth client credentials for a **Desktop app**.
   - Download the OAuth JSON as `client_secret.json` into this folder.

4. First auth/login:

   ```powershell
   python .\photo_pipeline.py auth
   ```

   A browser opens on your machine. Log in with the Google account you want to use.

5. Pixel ADB setup:

   - Enable Developer options on the Pixel.
   - Enable USB debugging.
   - Connect the Pixel by USB.
   - Approve the RSA prompt on the phone.
   - Check:

   ```powershell
   adb devices
   ```

## AI Product Recognition

API keys are read from `.env` or environment variables. Do not put API keys into `photo_pipeline.py`.

Create `.env` interactively:

```powershell
.\set_api_keys.ps1
```

Or create it manually:

```text
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
```

Default AI settings live in `config.json`:

```json
"mode": "ai",
"ai_provider": "both",
"openai_model": "gpt-4.1-mini",
"gemini_model": "gemini-2.5-flash"
```

To use only Gemini instead, set:

```json
"ai_provider": "gemini"
```

Supported values are `both`, `openai`, `gemini`, and `offline` from the web UI. In `both` mode, OpenAI and Gemini classify the same reference image; matching results are treated as agreement, and if one provider fails the other can still be used.

## Test Modes

## Web UI

Start the local web interface:

```powershell
python .\web_app.py
```

Open:

```text
http://127.0.0.1:8765
```

Optional internal domain:

```powershell
# Run PowerShell as Administrator first
.\add_internal_domain.ps1
```

Then open:

```text
http://pixel-agent.test:8765
```

The UI can:

- scan a local product folder for docs and sample images;
- classify the latest captured image;
- trigger Pixel photo capture and Google Photos upload with one button;
- trigger Pixel video recording and Google Photos upload with one button.

Start automatically when Windows logs in:

```powershell
.\install_startup_shortcut.ps1
```

Stop auto-start:

```powershell
.\uninstall_startup_shortcut.ps1
```

The Pixel Agent uses port `8765`, so it will not conflict with VietDub AI on port `3210`.

## Production Readiness

This repo is currently a local operator app / edge-agent prototype. For thousands of users, keep the Pixel/ADB capture worker local, but move shared product data and user management to a proper backend.

Recommended additions before multi-user production:

- authentication and role-based access control;
- per-user/per-device OAuth token storage with encryption;
- database-backed catalog instead of local `product_catalog.json`;
- background job queue for capture/classification/upload work;
- audit logs for every upload and classification decision;
- production WSGI server instead of Flask's development server;
- centralized error monitoring and retry policy;
- per-customer Google Photos/Drive quota handling;
- device registration so one user's browser cannot control another user's Pixel.

Recommended product folder layout:

```text
products/
|-- Product A/
|   |-- front.jpg
|   `-- barcode.jpg
|-- Product B/
|   `-- sample.jpg
`-- product-list.txt
```

Docs supported for product-name extraction: `.txt`, `.csv`, `.json`, `.docx`, `.pdf`. Images under a product folder are added as samples for that folder name.

Upload an existing photo and force a product name:

```powershell
python .\photo_pipeline.py upload .\inbox\test.jpg --product "My Product"
```

Capture from Pixel, classify, and upload:

```powershell
python .\photo_pipeline.py run-once --product "My Product"
```

Capture from Pixel, auto-classify from product samples, and upload:

```powershell
python .\photo_pipeline.py run-once-auto
```

Record a video from Pixel, auto-classify using a quick reference photo, and upload:

```powershell
python .\photo_pipeline.py record-once --duration 10
```

Run automatically every 30 seconds:

```powershell
python .\photo_pipeline.py watch --interval 30
```

Run automatically 5 times:

```powershell
python .\photo_pipeline.py watch --interval 30 --count 5
```

Capture only:

```powershell
python .\photo_pipeline.py capture
```

Classify by filename keywords from `product_labels.example.json`:

```powershell
python .\photo_pipeline.py run-once
```

For a real product test, edit `product_labels.example.json` with your SKU/product names and keywords, or pass `--product` while validating the upload flow.

## Offline Product Recognition

The current recognition module works offline by comparing a newly captured image against saved sample images. It is enough for initial testing when the product is framed consistently.

Add a sample image:

```powershell
python .\photo_pipeline.py add-sample --product "My Product" .\inbox\sample.jpg
```

Add 2-5 samples per product from slightly different angles. Samples are copied under `samples/`, and metadata is stored in `product_catalog.json`.

Test classification without upload:

```powershell
python .\photo_pipeline.py classify .\inbox\test.jpg
```

If the match score is below `similarity_threshold` in `config.json`, the product becomes `Unsorted`.
