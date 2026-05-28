from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template_string, request

import photo_pipeline as pipeline


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"

app = Flask(__name__)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
DOC_EXTS = {".txt", ".csv", ".json", ".docx", ".pdf"}


HTML = r"""
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pixel Product Capture</title>
  <style>
    :root { color-scheme: light; font-family: Arial, sans-serif; }
    body { margin: 0; background: #f5f6f8; color: #1f2937; }
    header { background: #ffffff; border-bottom: 1px solid #d7dce3; padding: 16px 24px; }
    main { max-width: 1120px; margin: 0 auto; padding: 24px; display: grid; gap: 18px; }
    section { background: #ffffff; border: 1px solid #d7dce3; border-radius: 8px; padding: 18px; }
    h1 { margin: 0; font-size: 22px; }
    h2 { margin: 0 0 14px; font-size: 17px; }
    label { display: block; font-weight: 700; margin-bottom: 8px; }
    input, select, button { font: inherit; }
    input, select { width: 100%; box-sizing: border-box; padding: 10px 12px; border: 1px solid #aeb7c4; border-radius: 6px; }
    button { border: 0; border-radius: 6px; padding: 10px 14px; background: #155eef; color: white; cursor: pointer; font-weight: 700; }
    button.secondary { background: #475467; }
    button:disabled { opacity: .55; cursor: wait; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .row { display: flex; gap: 10px; align-items: end; }
    .row > div { flex: 1; }
    .status { white-space: pre-wrap; background: #111827; color: #e5e7eb; padding: 14px; border-radius: 6px; min-height: 120px; overflow: auto; }
    .pill { display: inline-block; background: #eef2ff; color: #3730a3; border-radius: 999px; padding: 4px 9px; margin: 3px; font-size: 13px; }
    .muted { color: #667085; font-size: 13px; }
    @media (max-width: 780px) { .grid, .row { grid-template-columns: 1fr; display: grid; } }
  </style>
</head>
<body>
  <header>
    <h1>Pixel Product Capture</h1>
    <div class="muted">Chụp từ Google Pixel, AI nhận diện sản phẩm, tạo album Google Photos và upload tự động.</div>
  </header>
  <main>
    <section>
      <h2>Trạng Thái</h2>
      <div id="health" class="muted">Đang kiểm tra...</div>
    </section>

    <section>
      <h2>Nạp Dữ Liệu Sản Phẩm</h2>
      <div class="row">
        <div>
          <label for="sourcePath">Đường dẫn thư mục tài liệu / hình ảnh sản phẩm</label>
          <input id="sourcePath" placeholder="Ví dụ: D:\product-data">
          <div class="muted">Gợi ý: mỗi sản phẩm một thư mục riêng, ví dụ <b>products\Tên Sản Phẩm\anh1.jpg</b>. File .txt/.csv/.json/.docx/.pdf có thể chứa tên sản phẩm mỗi dòng.</div>
        </div>
        <button id="ingestBtn" onclick="ingest()">Quét Dữ Liệu</button>
      </div>
      <div style="height:10px"></div>
      <button class="secondary" onclick="resetCatalog()">Xóa Catalog Và Quét Lại</button>
    </section>

    <section>
      <h2>Chụp Và Upload</h2>
      <div class="grid">
        <div>
          <label for="provider">AI provider</label>
          <select id="provider">
            <option value="openai">OpenAI</option>
            <option value="gemini">Gemini</option>
            <option value="offline">Offline mẫu ảnh</option>
          </select>
        </div>
        <div>
          <label for="forcedProduct">Ép tên sản phẩm nếu muốn test</label>
          <input id="forcedProduct" placeholder="Để trống để AI tự nhận diện">
        </div>
      </div>
      <div style="height:12px"></div>
      <div class="row">
        <button id="captureBtn" onclick="captureUpload()">Chụp Từ Pixel Và Upload</button>
        <button class="secondary" onclick="classifyLatest()">Nhận Diện Ảnh Mới Nhất</button>
      </div>
    </section>

    <section>
      <h2>Sản Phẩm Đã Nạp</h2>
      <div id="products"></div>
    </section>

    <section>
      <h2>Log</h2>
      <div id="log" class="status"></div>
    </section>
  </main>

  <script>
    const logBox = document.getElementById("log");
    function log(value) {
      const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
      logBox.textContent = text + "\n\n" + logBox.textContent;
    }
    async function api(path, body) {
      const res = await fetch(path, {
        method: body ? "POST" : "GET",
        headers: body ? {"Content-Type": "application/json"} : {},
        body: body ? JSON.stringify(body) : undefined
      });
      const data = await res.json();
      if (!res.ok) throw data;
      return data;
    }
    async function refresh() {
      try {
        const data = await api("/api/status");
        document.getElementById("health").textContent =
          `ADB: ${data.adb_device || "chưa thấy Pixel"} | Google token: ${data.google_token ? "có" : "chưa có"} | AI: ${data.ai_provider}`;
        document.getElementById("provider").value = data.ai_provider;
        document.getElementById("products").innerHTML = data.products.map(p => `<span class="pill">${p}</span>`).join("") || "<span class='muted'>Chưa có sản phẩm</span>";
      } catch (err) { log(err); }
    }
    async function ingest() {
      const btn = document.getElementById("ingestBtn");
      btn.disabled = true;
      try {
        const data = await api("/api/ingest", {source_path: document.getElementById("sourcePath").value});
        log(data);
        await refresh();
      } catch (err) { log(err); } finally { btn.disabled = false; }
    }
    async function captureUpload() {
      const btn = document.getElementById("captureBtn");
      btn.disabled = true;
      try {
        const data = await api("/api/capture-upload", {
          provider: document.getElementById("provider").value,
          product: document.getElementById("forcedProduct").value
        });
        log(data);
        await refresh();
      } catch (err) { log(err); } finally { btn.disabled = false; }
    }
    async function classifyLatest() {
      try {
        const data = await api("/api/classify-latest", {provider: document.getElementById("provider").value});
        log(data);
      } catch (err) { log(err); }
    }
    async function resetCatalog() {
      if (!confirm("Xóa toàn bộ catalog sản phẩm đã nạp?")) return;
      try {
        const data = await api("/api/reset-catalog", {});
        log(data);
        await refresh();
      } catch (err) { log(err); }
    }
    refresh();
  </script>
</body>
</html>
"""


def settings() -> pipeline.Settings:
    loaded = pipeline.load_settings(CONFIG_PATH)
    pipeline.load_dotenv(loaded.root)
    pipeline.ensure_dirs(loaded)
    return loaded


def error_response(exc: Exception, status: int = 500):
    return jsonify({"error": str(exc)}), status


def read_doc_text(path: Path) -> str:
    if path.suffix.lower() in {".txt", ".csv"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return json.dumps(data, ensure_ascii=False)
    if path.suffix.lower() == ".docx":
        from docx import Document

        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return ""


def names_from_text(text: str) -> list[str]:
    names: list[str] = []
    for line in text.splitlines():
        cleaned = line.lstrip("\ufeff").strip(" \t,-;|")
        if not cleaned or len(cleaned) < 2:
            continue
        if any(token in cleaned for token in ["{", "}", ">=", "://", "\\", "/"]):
            continue
        if any(label in cleaned.lower() for label in ["product", "san pham", "sản phẩm", "ten san pham", "tên sản phẩm", "sku"]):
            parts = [part.strip() for part in cleaned.replace("|", ",").split(",") if part.strip()]
            cleaned = parts[-1] if parts else cleaned
        if len(cleaned) <= 100 and cleaned not in names:
            names.append(cleaned)
    return names


def ingest_source(source_path: Path, cfg: pipeline.Settings) -> dict[str, Any]:
    if not source_path.exists():
        raise ValueError(f"Khong thay duong dan: {source_path}")
    if not source_path.is_dir():
        raise ValueError("Hay chon/nhap mot thu muc, khong phai mot file.")

    added_names: list[str] = []
    added_samples: list[dict[str, str]] = []
    root_doc_names = {"danh-sach-san-pham", "product-list", "products", "catalog", "sku-list"}

    for path in source_path.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in IMAGE_EXTS:
            product_name = path.parent.name if path.parent != source_path else path.stem
            pipeline.add_sample(cfg, product_name, path)
            if product_name not in added_names:
                added_names.append(product_name)
            added_samples.append({"product": product_name, "image": str(path)})
        elif suffix in DOC_EXTS:
            catalog = pipeline.load_catalog(cfg)
            if path.parent != source_path:
                product_name = path.parent.name
                pipeline.find_or_create_product(catalog, product_name)
                if product_name not in added_names:
                    added_names.append(product_name)
            elif path.stem.lower() in root_doc_names:
                for name in names_from_text(read_doc_text(path)):
                    pipeline.find_or_create_product(catalog, name)
                    if name not in added_names:
                        added_names.append(name)
            pipeline.save_catalog(cfg, catalog)

    return {"added_products": added_names, "added_samples": added_samples, "count_samples": len(added_samples)}


def set_provider(cfg: pipeline.Settings, provider: str) -> None:
    provider = provider.lower().strip()
    if provider == "offline":
        cfg.classification_mode = "image_similarity"
        return
    if provider in {"openai", "gemini"}:
        cfg.classification_mode = "ai"
        cfg.ai_provider = provider
        return
    raise ValueError(f"Provider khong hop le: {provider}")


def latest_inbox_image(cfg: pipeline.Settings) -> Path:
    images = [p for p in cfg.inbox_dir.glob("*") if p.suffix.lower() in IMAGE_EXTS]
    if not images:
        raise ValueError("Chua co anh trong inbox.")
    return max(images, key=lambda p: p.stat().st_mtime)


@app.get("/")
def index():
    return render_template_string(HTML)


@app.get("/api/status")
def api_status():
    cfg = settings()
    adb = pipeline.adb_command(cfg, "devices", check=False).stdout.splitlines()
    devices = [line.split()[0] for line in adb if "\tdevice" in line]
    return jsonify(
        {
            "adb_device": devices[0] if devices else "",
            "google_token": cfg.token_file.exists(),
            "ai_provider": cfg.ai_provider if cfg.classification_mode == "ai" else "offline",
            "products": pipeline.product_names(cfg),
        }
    )


@app.post("/api/ingest")
def api_ingest():
    try:
        cfg = settings()
        source = Path(request.json.get("source_path", "")).expanduser()
        return jsonify(ingest_source(source, cfg))
    except Exception as exc:
        return error_response(exc)


@app.post("/api/reset-catalog")
def api_reset_catalog():
    try:
        cfg = settings()
        pipeline.save_catalog(cfg, {"products": []})
        return jsonify({"status": "reset", "catalog": str(cfg.catalog_file)})
    except Exception as exc:
        return error_response(exc)


@app.post("/api/classify-latest")
def api_classify_latest():
    try:
        cfg = settings()
        set_provider(cfg, request.json.get("provider", cfg.ai_provider))
        image = latest_inbox_image(cfg)
        product, score, reason = pipeline.classify_product(cfg, image)
        return jsonify({"image": str(image), "product": product, "score": score, "reason": reason})
    except Exception as exc:
        return error_response(exc)


@app.post("/api/capture-upload")
def api_capture_upload():
    try:
        cfg = settings()
        set_provider(cfg, request.json.get("provider", cfg.ai_provider))
        forced_product = (request.json.get("product") or "").strip() or None
        image = pipeline.capture_from_pixel(cfg)
        product, score, reason = pipeline.classify_product(cfg, image, forced_product)
        result = pipeline.upload_photo(cfg, image, product)
        return jsonify(
            {
                "captured": str(image),
                "product": product,
                "score": score,
                "reason": reason,
                **pipeline.upload_result_summary(result),
            }
        )
    except Exception as exc:
        return error_response(exc)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8765")), debug=False)
