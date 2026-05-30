from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from PIL import Image, ImageOps


PHOTOS_SCOPE = "https://www.googleapis.com/auth/photoslibrary.appendonly"
API_BASE = "https://photoslibrary.googleapis.com/v1"
UPLOAD_URL = "https://photoslibrary.googleapis.com/v1/uploads"


@dataclass
class Settings:
    root: Path
    client_secret_file: Path
    token_file: Path
    album_cache_file: Path
    inbox_dir: Path
    processed_dir: Path
    labels_file: Path
    catalog_file: Path
    default_product: str
    similarity_threshold: float
    classification_mode: str
    ai_provider: str
    openai_model: str
    gemini_model: str
    adb_serial: str
    camera_dir: str


def load_settings(config_path: Path) -> Settings:
    if not config_path.exists():
        raise SystemExit(f"Missing {config_path}. Copy config.example.json to config.json first.")

    root = config_path.parent.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))

    def resolve(value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else root / path

    return Settings(
        root=root,
        client_secret_file=resolve(config["google"]["client_secret_file"]),
        token_file=resolve(config["google"]["token_file"]),
        album_cache_file=resolve(config["google"]["album_cache_file"]),
        inbox_dir=resolve(config["paths"]["inbox_dir"]),
        processed_dir=resolve(config["paths"]["processed_dir"]),
        labels_file=resolve(config["classification"]["labels_file"]),
        catalog_file=resolve(config["classification"].get("catalog_file", "product_catalog.json")),
        default_product=config["classification"].get("default_product", "Unsorted"),
        similarity_threshold=float(config["classification"].get("similarity_threshold", 0.82)),
        classification_mode=config["classification"].get("mode", "image_similarity"),
        ai_provider=config["classification"].get("ai_provider", "openai"),
        openai_model=config["classification"].get("openai_model", "gpt-4.1-mini"),
        gemini_model=config["classification"].get("gemini_model", "gemini-2.5-flash"),
        adb_serial=config["pixel"].get("adb_serial", ""),
        camera_dir=config["pixel"].get("camera_dir", "/sdcard/DCIM/Camera"),
    )


def ensure_dirs(settings: Settings) -> None:
    settings.inbox_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_dir.mkdir(parents=True, exist_ok=True)


def load_dotenv(root: Path) -> None:
    env_path = root / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def get_credentials(settings: Settings) -> Credentials:
    creds: Credentials | None = None
    if settings.token_file.exists():
        creds = Credentials.from_authorized_user_file(str(settings.token_file), [PHOTOS_SCOPE])

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not settings.client_secret_file.exists():
            raise SystemExit(
                f"Missing {settings.client_secret_file}. Download OAuth Desktop credentials as client_secret.json."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(settings.client_secret_file), [PHOTOS_SCOPE])
        creds = flow.run_local_server(port=0)

    settings.token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


def auth_headers(creds: Credentials) -> dict[str, str]:
    return {"Authorization": f"Bearer {creds.token}"}


def load_album_cache(settings: Settings) -> dict[str, str]:
    if not settings.album_cache_file.exists():
        return {}
    return json.loads(settings.album_cache_file.read_text(encoding="utf-8"))


def save_album_cache(settings: Settings, cache: dict[str, str]) -> None:
    settings.album_cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def create_album(settings: Settings, creds: Credentials, title: str) -> str:
    response = requests.post(
        f"{API_BASE}/albums",
        headers={**auth_headers(creds), "Content-Type": "application/json"},
        json={"album": {"title": title}},
        timeout=60,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Create album failed: {response.status_code} {response.text}")
    album_id = response.json()["id"]
    cache = load_album_cache(settings)
    cache[title] = album_id
    save_album_cache(settings, cache)
    return album_id


def get_or_create_album(settings: Settings, creds: Credentials, title: str) -> str:
    cache = load_album_cache(settings)
    if title in cache:
        return cache[title]
    return create_album(settings, creds, title)


def upload_bytes(creds: Credentials, image_path: Path) -> str:
    mime_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
    response = requests.post(
        UPLOAD_URL,
        headers={
            **auth_headers(creds),
            "Content-Type": "application/octet-stream",
            "X-Goog-Upload-File-Name": image_path.name,
            "X-Goog-Upload-Protocol": "raw",
        },
        data=image_path.read_bytes(),
        timeout=120,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Upload bytes failed ({mime_type}): {response.status_code} {response.text}")
    return response.text


def create_media_item(creds: Credentials, upload_token: str, album_id: str, description: str) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE}/mediaItems:batchCreate",
        headers={**auth_headers(creds), "Content-Type": "application/json"},
        json={
            "albumId": album_id,
            "newMediaItems": [
                {
                    "description": description,
                    "simpleMediaItem": {"uploadToken": upload_token},
                }
            ],
        },
        timeout=120,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Create media item failed: {response.status_code} {response.text}")
    return response.json()


def classify_by_filename(settings: Settings, image_path: Path, forced_product: str | None) -> str:
    if forced_product:
        return forced_product

    if settings.labels_file.exists():
        labels = json.loads(settings.labels_file.read_text(encoding="utf-8"))
        haystack = image_path.name.lower()
        for product in labels.get("products", []):
            for keyword in product.get("keywords", []):
                if keyword.lower() in haystack:
                    return product["name"]

    return settings.default_product


def image_average_hash(image_path: Path, size: int = 16) -> str:
    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image)
        image = image.convert("L").resize((size, size))
        pixels = list(image.getdata())
    avg = sum(pixels) / len(pixels)
    return "".join("1" if pixel >= avg else "0" for pixel in pixels)


def hash_similarity(left: str, right: str) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    matches = sum(1 for a, b in zip(left, right) if a == b)
    return matches / len(left)


def load_catalog(settings: Settings) -> dict[str, Any]:
    if not settings.catalog_file.exists():
        return {"products": []}
    return json.loads(settings.catalog_file.read_text(encoding="utf-8"))


def save_catalog(settings: Settings, catalog: dict[str, Any]) -> None:
    settings.catalog_file.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")


def find_or_create_product(catalog: dict[str, Any], name: str) -> dict[str, Any]:
    for product in catalog.setdefault("products", []):
        if product.get("name") == name:
            product.setdefault("samples", [])
            return product
    product = {"name": name, "samples": []}
    catalog["products"].append(product)
    return product


def add_sample(settings: Settings, product_name: str, image_path: Path) -> dict[str, Any]:
    catalog = load_catalog(settings)
    product = find_or_create_product(catalog, product_name)

    samples_dir = settings.root / "samples" / safe_name(product_name)
    samples_dir.mkdir(parents=True, exist_ok=True)
    target = samples_dir / image_path.name
    if image_path.resolve() != target.resolve():
        shutil.copy2(image_path, target)

    sample = {
        "path": str(target.relative_to(settings.root)),
        "hash": image_average_hash(target),
    }
    for existing in product["samples"]:
        if existing.get("path") == sample["path"]:
            existing.update(sample)
            save_catalog(settings, catalog)
            return existing
    product["samples"].append(sample)
    save_catalog(settings, catalog)
    return sample


def classify_by_samples(settings: Settings, image_path: Path) -> tuple[str, float]:
    catalog = load_catalog(settings)
    image_hash = image_average_hash(image_path)
    best_product = settings.default_product
    best_score = 0.0

    for product in catalog.get("products", []):
        for sample in product.get("samples", []):
            sample_hash = sample.get("hash")
            if not sample_hash and sample.get("path"):
                sample_path = settings.root / sample["path"]
                if sample_path.exists():
                    sample_hash = image_average_hash(sample_path)
                    sample["hash"] = sample_hash
            score = hash_similarity(image_hash, sample_hash or "")
            if score > best_score:
                best_score = score
                best_product = product.get("name", settings.default_product)

    if best_score < settings.similarity_threshold:
        best_product = settings.default_product

    save_catalog(settings, catalog)
    return best_product, best_score


def product_names(settings: Settings) -> list[str]:
    names: list[str] = []
    catalog = load_catalog(settings)
    for product in catalog.get("products", []):
        name = product.get("name")
        if name and name not in names:
            names.append(name)
    if settings.labels_file.exists():
        labels = json.loads(settings.labels_file.read_text(encoding="utf-8"))
        for product in labels.get("products", []):
            name = product.get("name")
            if name and name not in names:
                names.append(name)
    if settings.default_product not in names:
        names.append(settings.default_product)
    return names


def image_data_url(image_path: Path) -> str:
    mime_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def ai_prompt(names: list[str]) -> str:
    product_list = "\n".join(f"- {name}" for name in names)
    return (
        "You are classifying a product photo for automatic Google Photos album upload.\n"
        "Pick exactly one product name from the allowed list below. If none match clearly, pick Unsorted.\n"
        "Return strict JSON only with keys: product, confidence, reason.\n\n"
        f"Allowed products:\n{product_list}\n"
    )


def parse_ai_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def classify_with_openai(settings: Settings, image_path: Path, names: list[str]) -> tuple[str, float | None, str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Put it in .env or set it in PowerShell.")

    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": settings.openai_model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": ai_prompt(names)},
                        {"type": "input_image", "image_url": image_data_url(image_path), "detail": "low"},
                    ],
                }
            ],
        },
        timeout=120,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"OpenAI classification failed: {response.status_code} {response.text}")
    payload = response.json()
    text = payload.get("output_text")
    if not text:
        parts: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    parts.append(content.get("text", ""))
        text = "\n".join(parts)
    parsed = parse_ai_json(text)
    product = parsed.get("product", settings.default_product)
    if product not in names:
        product = settings.default_product
    return product, parsed.get("confidence"), parsed.get("reason", "")


def classify_with_gemini(settings: Settings, image_path: Path, names: list[str]) -> tuple[str, float | None, str]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Put it in .env or set it in PowerShell.")

    mime_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    response = requests.post(
        url,
        params={"key": api_key},
        headers={"Content-Type": "application/json"},
        json={
            "contents": [
                {
                    "parts": [
                        {"text": ai_prompt(names)},
                        {"inline_data": {"mime_type": mime_type, "data": encoded}},
                    ]
                }
            ],
            "generationConfig": {"response_mime_type": "application/json"},
        },
        timeout=120,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Gemini classification failed: {response.status_code} {response.text}")
    payload = response.json()
    text = payload["candidates"][0]["content"]["parts"][0]["text"]
    parsed = parse_ai_json(text)
    product = parsed.get("product", settings.default_product)
    if product not in names:
        product = settings.default_product
    return product, parsed.get("confidence"), parsed.get("reason", "")


def classify_by_ai(settings: Settings, image_path: Path) -> tuple[str, float | None, str]:
    names = product_names(settings)
    provider = settings.ai_provider.lower()
    if provider in {"both", "openai+gemini", "dual"}:
        results: list[tuple[str, float | None, str, str]] = []
        errors: list[str] = []
        for name, classifier in (("openai", classify_with_openai), ("gemini", classify_with_gemini)):
            try:
                product, confidence, reason = classifier(settings, image_path, names)
                results.append((name, product, confidence, reason))
            except Exception as exc:
                errors.append(f"{name}: {exc}")
        if not results:
            raise RuntimeError("; ".join(errors) or "No AI provider returned a result.")

        non_unsorted = [result for result in results if result[1] != settings.default_product]
        if len(non_unsorted) >= 2 and len({result[1] for result in non_unsorted}) == 1:
            provider_names = "+".join(result[0] for result in non_unsorted)
            confidence_values = [result[2] for result in non_unsorted if isinstance(result[2], int | float)]
            avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else None
            return non_unsorted[0][1], avg_confidence, f"{provider_names} agreed: {non_unsorted[0][3]}"

        chosen = max(
            results,
            key=lambda result: (result[1] != settings.default_product, float(result[2] or 0)),
        )
        extra = f"; errors: {'; '.join(errors)}" if errors else ""
        return chosen[1], chosen[2], f"{chosen[0]} selected; dual results={[(r[0], r[1], r[2]) for r in results]}{extra}"
    if provider == "gemini":
        return classify_with_gemini(settings, image_path, names)
    if provider == "openai":
        return classify_with_openai(settings, image_path, names)
    raise RuntimeError(f"Unsupported ai_provider: {settings.ai_provider}")


def classify_product(settings: Settings, image_path: Path, forced_product: str | None = None) -> tuple[str, float | None, str]:
    if forced_product:
        return forced_product, None, "forced by user"
    if settings.classification_mode == "ai":
        try:
            return classify_by_ai(settings, image_path)
        except Exception as exc:
            product, score = classify_by_samples(settings, image_path)
            if product != settings.default_product:
                return product, score, f"AI failed; used sample match: {exc}"
            filename_product = classify_by_filename(settings, image_path, None)
            return filename_product, score, f"AI failed; used fallback: {exc}"
    product, score = classify_by_samples(settings, image_path)
    if product != settings.default_product:
        return product, score, "sample match"
    filename_product = classify_by_filename(settings, image_path, None)
    return filename_product, score, "filename fallback"


def adb_command(settings: Settings, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = ["adb"]
    if settings.adb_serial:
        command += ["-s", settings.adb_serial]
    command += list(args)
    return subprocess.run(command, text=True, capture_output=True, check=check)


def capture_from_pixel(settings: Settings) -> Path:
    ensure_dirs(settings)
    before_latest = adb_command(
        settings,
        "shell",
        f"ls -t {settings.camera_dir}/*.jpg {settings.camera_dir}/*.jpeg 2>/dev/null | head -n 1",
        check=False,
    ).stdout.strip()

    adb_command(settings, "shell", "am", "start", "-a", "android.media.action.STILL_IMAGE_CAMERA")
    time.sleep(2)
    adb_command(settings, "shell", "input", "keyevent", "27")

    latest = ""
    for _ in range(12):
        time.sleep(1)
        latest = adb_command(
            settings,
            "shell",
            f"ls -t {settings.camera_dir}/*.jpg {settings.camera_dir}/*.jpeg 2>/dev/null | head -n 1",
            check=False,
        ).stdout.strip()
        if latest and latest != before_latest:
            break

    if not latest:
        raise RuntimeError("Could not find a captured JPG/JPEG in the Pixel camera folder.")
    if latest == before_latest:
        raise RuntimeError("Pixel did not create a new photo. Check Camera app focus/permissions and try again.")

    local_path = settings.inbox_dir / Path(latest).name
    adb_command(settings, "pull", latest, str(local_path))
    return local_path


def capture_video_from_pixel(settings: Settings, duration_seconds: int = 10) -> Path:
    ensure_dirs(settings)
    duration_seconds = max(1, min(duration_seconds, 300))
    before_latest = adb_command(
        settings,
        "shell",
        f"ls -t {settings.camera_dir}/*.mp4 {settings.camera_dir}/*.3gp 2>/dev/null | head -n 1",
        check=False,
    ).stdout.strip()

    adb_command(settings, "shell", "am", "start", "-a", "android.media.action.VIDEO_CAMERA")
    time.sleep(2)
    adb_command(settings, "shell", "input", "keyevent", "27")
    time.sleep(duration_seconds)
    adb_command(settings, "shell", "input", "keyevent", "27")

    latest = ""
    for _ in range(20):
        time.sleep(1)
        latest = adb_command(
            settings,
            "shell",
            f"ls -t {settings.camera_dir}/*.mp4 {settings.camera_dir}/*.3gp 2>/dev/null | head -n 1",
            check=False,
        ).stdout.strip()
        if latest and latest != before_latest:
            break

    if not latest:
        raise RuntimeError("Could not find a captured MP4/3GP in the Pixel camera folder.")
    if latest == before_latest:
        raise RuntimeError("Pixel did not create a new video. Check Camera app focus/permissions and try again.")

    local_path = settings.inbox_dir / Path(latest).name
    adb_command(settings, "pull", latest, str(local_path))
    return local_path


def upload_photo(settings: Settings, image_path: Path, product: str) -> dict[str, Any]:
    creds = get_credentials(settings)
    album_id = get_or_create_album(settings, creds, product)
    upload_token = upload_bytes(creds, image_path)
    result = create_media_item(creds, upload_token, album_id, f"Product: {product}")

    product_dir = settings.processed_dir / safe_name(product)
    product_dir.mkdir(parents=True, exist_ok=True)
    target = product_dir / image_path.name
    if image_path.resolve() != target.resolve():
        shutil.copy2(image_path, target)
    return {"album_id": album_id, "api_result": result}


def upload_media(settings: Settings, media_path: Path, product: str, description_prefix: str = "Product") -> dict[str, Any]:
    creds = get_credentials(settings)
    album_id = get_or_create_album(settings, creds, product)
    upload_token = upload_bytes(creds, media_path)
    result = create_media_item(creds, upload_token, album_id, f"{description_prefix}: {product}")

    product_dir = settings.processed_dir / safe_name(product)
    product_dir.mkdir(parents=True, exist_ok=True)
    target = product_dir / media_path.name
    if media_path.resolve() != target.resolve():
        shutil.copy2(media_path, target)
    return {"album_id": album_id, "api_result": result}


def print_upload_summary(payload: dict[str, Any]) -> None:
    result = payload.get("api_result", payload)
    media_results = result.get("newMediaItemResults", [])
    media_item = media_results[0].get("mediaItem", {}) if media_results else {}
    status = media_results[0].get("status", {}) if media_results else {}
    summary = {
        "product": payload.get("product"),
        "match_score": payload.get("match_score"),
        "classification_reason": payload.get("classification_reason"),
        "captured": payload.get("captured"),
        "album_id": payload.get("album_id"),
        "status": status.get("message"),
        "filename": media_item.get("filename"),
        "photo_url": media_item.get("productUrl"),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if media_item.get("productUrl"):
        print(f"\nOpen this Google Photos link:\n{media_item['productUrl']}")


def upload_result_summary(payload: dict[str, Any]) -> dict[str, Any]:
    result = payload.get("api_result", payload)
    media_results = result.get("newMediaItemResults", [])
    media_item = media_results[0].get("mediaItem", {}) if media_results else {}
    status = media_results[0].get("status", {}) if media_results else {}
    return {
        "album_id": payload.get("album_id"),
        "status": status.get("message"),
        "filename": media_item.get("filename"),
        "photo_url": media_item.get("productUrl"),
    }


def safe_name(value: str) -> str:
    return "".join(c if c.isalnum() or c in " ._-" else "_" for c in value).strip() or "Unsorted"


def cmd_auth(settings: Settings, _args: argparse.Namespace) -> None:
    get_credentials(settings)
    print(f"Authenticated. Token stored at {settings.token_file}")


def cmd_capture(settings: Settings, _args: argparse.Namespace) -> None:
    path = capture_from_pixel(settings)
    print(path)


def cmd_upload(settings: Settings, args: argparse.Namespace) -> None:
    image_path = Path(args.image).resolve()
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")
    product, score, reason = classify_product(settings, image_path, args.product)
    result = upload_photo(settings, image_path, product)
    print_upload_summary({"product": product, "match_score": score, "classification_reason": reason, **result})


def cmd_run_once(settings: Settings, args: argparse.Namespace) -> None:
    image_path = capture_from_pixel(settings)
    product, score, reason = classify_product(settings, image_path, args.product)
    result = upload_photo(settings, image_path, product)
    print_upload_summary(
        {"captured": str(image_path), "product": product, "match_score": score, "classification_reason": reason, **result}
    )


def cmd_record_once(settings: Settings, args: argparse.Namespace) -> None:
    reference_path: Path | None = None
    if args.product:
        product, score, reason = args.product, None, "forced by user"
    else:
        reference_path = capture_from_pixel(settings)
        product, score, reason = classify_product(settings, reference_path)
    video_path = capture_video_from_pixel(settings, args.duration)
    result = upload_media(settings, video_path, product, "Product video")
    print_upload_summary(
        {
            "captured": str(video_path),
            "reference_image": str(reference_path) if reference_path else None,
            "product": product,
            "match_score": score,
            "classification_reason": reason,
            **result,
        }
    )


def cmd_classify(settings: Settings, args: argparse.Namespace) -> None:
    image_path = Path(args.image).resolve()
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")
    product, score, reason = classify_product(settings, image_path, args.product)
    print(
        json.dumps(
            {"image": str(image_path), "product": product, "match_score": score, "classification_reason": reason},
            indent=2,
            ensure_ascii=False,
        )
    )


def cmd_add_sample(settings: Settings, args: argparse.Namespace) -> None:
    image_path = Path(args.image).resolve()
    if not image_path.exists():
        raise SystemExit(f"Image not found: {image_path}")
    sample = add_sample(settings, args.product, image_path)
    print(json.dumps({"product": args.product, "sample": sample}, indent=2, ensure_ascii=False))


def cmd_watch(settings: Settings, args: argparse.Namespace) -> None:
    count = 0
    while args.count <= 0 or count < args.count:
        count += 1
        print(f"\nRun {count}: capturing and uploading...")
        cmd_run_once(settings, args)
        if args.count > 0 and count >= args.count:
            break
        time.sleep(args.interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pixel capture to Google Photos product albums.")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("auth", help="Authorize Google Photos API access")
    subparsers.add_parser("capture", help="Capture one photo from Pixel via ADB")

    upload = subparsers.add_parser("upload", help="Upload an existing image")
    upload.add_argument("image")
    upload.add_argument("--product", help="Force product/album name")

    run_once = subparsers.add_parser("run-once", help="Capture, classify, and upload one photo")
    run_once.add_argument("--product", help="Force product/album name")

    run_once_auto = subparsers.add_parser("run-once-auto", help="Capture, auto-classify from samples, and upload one photo")
    run_once_auto.set_defaults(command="run-once")

    record_once = subparsers.add_parser("record-once", help="Record, classify, and upload one video")
    record_once.add_argument("--product", help="Force product/album name")
    record_once.add_argument("--duration", type=int, default=10, help="Video duration in seconds")

    classify = subparsers.add_parser("classify", help="Classify an existing image without uploading")
    classify.add_argument("image")
    classify.add_argument("--product", help="Force product name")

    add_sample_parser = subparsers.add_parser("add-sample", help="Add a product sample image for offline recognition")
    add_sample_parser.add_argument("--product", required=True, help="Product/album name")
    add_sample_parser.add_argument("image")

    watch = subparsers.add_parser("watch", help="Repeatedly capture, auto-classify, and upload")
    watch.add_argument("--interval", type=int, default=30, help="Seconds between captures")
    watch.add_argument("--count", type=int, default=0, help="Number of captures; 0 means run forever")
    watch.add_argument("--product", help="Force product/album name for every capture")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings(Path(args.config).resolve())
    load_dotenv(settings.root)
    ensure_dirs(settings)

    handlers = {
        "auth": cmd_auth,
        "capture": cmd_capture,
        "upload": cmd_upload,
        "run-once": cmd_run_once,
        "run-once-auto": cmd_run_once,
        "record-once": cmd_record_once,
        "classify": cmd_classify,
        "add-sample": cmd_add_sample,
        "watch": cmd_watch,
    }
    handlers[args.command](settings, args)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(exc.stderr or exc.stdout, file=sys.stderr)
        raise SystemExit(exc.returncode)
