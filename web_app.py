from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template_string, request

import photo_pipeline as pipeline


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
DEFAULT_DRIVE_ROOT = r"G:\My Drive\Test hình ảnh shopee"
EVENT_LOCK = threading.Lock()
EVENTS: list[dict[str, Any]] = []
EVENT_COUNTER = 0
OPERATION_LOCK = threading.Lock()
CONFIG_LOCK = threading.RLock()

app = Flask(__name__)


HTML = r"""
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pixel Drive Capture</title>
  <style>
    :root {
      color-scheme: light;
      --bg:#f3f6fa; --panel:#fff; --soft:#f8fafc; --line:#d6deea;
      --text:#172033; --muted:#65758b; --brand:#155eef; --brand2:#0f47c5;
      --side:#0f172a; --ok:#137333; --okbg:#eaf7ef; --warn:#a15c00; --warnbg:#fff6e5;
      --shadow:0 8px 24px rgba(16,24,40,.07);
      font-family:Inter,"Segoe UI",Arial,sans-serif;
    }
    *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text)}
    button,input,select{font:inherit} button{min-height:40px;border:0;border-radius:7px;padding:10px 14px;background:var(--brand);color:#fff;font-weight:700;cursor:pointer;white-space:nowrap}
    button:hover{background:var(--brand2)} button:disabled{opacity:.58;cursor:wait}
    button.secondary{background:#455468} button.secondary:hover{background:#344054}
    button.ghost{background:#edf2f7;color:#243041} button.ghost:hover{background:#e2e8f0}
    button.danger{background:#b42318} button.danger:hover{background:#912018}
    input,select{width:100%;min-height:42px;border:1px solid #b9c5d5;border-radius:7px;background:#fff;padding:10px 12px;color:var(--text);outline:none}
    input:focus,select:focus{border-color:var(--brand);box-shadow:0 0 0 3px rgba(21,94,239,.12)}
    label{display:block;margin-bottom:7px;font-weight:700}.shell{min-height:100vh}
    .sidebar{display:none}
    .brand{padding-bottom:21px;border-bottom:1px solid rgba(255,255,255,.14)} .brand h1{font-size:18px;margin:0 0 6px}.brand p{font-size:13px;color:#a9b4c7;line-height:1.45;margin:0}
    .nav{display:grid;gap:7px;margin-top:20px}.nav div{display:flex;justify-content:space-between;gap:8px;padding:10px;border-radius:7px;color:#cbd5e1;font-size:14px}.nav .active{background:rgba(255,255,255,.1);color:#fff}
    .main{min-width:0}.topbar{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:17px 26px;background:rgba(255,255,255,.9);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:3;backdrop-filter:blur(10px)}
    .topbar h2{margin:0;font-size:22px}.topbar p{margin:4px 0 0;color:var(--muted);font-size:14px}.actions,.buttons{display:flex;gap:10px;flex-wrap:wrap}
    .content{padding:20px 26px 40px}.workspace{display:grid;grid-template-columns:minmax(0,1fr) 430px;gap:18px;align-items:start}.work-main{display:grid;gap:18px;min-width:0}.work-log{position:sticky;top:94px;min-width:0}.metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}
    .metric,.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;box-shadow:var(--shadow)}.metric{padding:15px;min-height:91px}.metric small{display:block;color:var(--muted);font-size:12px;font-weight:700;text-transform:uppercase}.metric strong{display:block;margin-top:8px;font-size:16px;overflow-wrap:anywhere}
    .badge{display:inline-flex;min-height:25px;align-items:center;border-radius:999px;padding:4px 9px;font-size:13px;font-weight:700}.ok{background:var(--okbg);color:var(--ok)}.warn{background:var(--warnbg);color:var(--warn)}
    .layout{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(320px,.65fr);gap:18px;align-items:start}.panel{overflow:hidden}.panel-head{padding:16px 18px;border-bottom:1px solid var(--line)}.panel-head h3{margin:0;font-size:17px}.panel-head p{margin:4px 0 0;color:var(--muted);font-size:13px;line-height:1.45}.panel-body{padding:18px;display:grid;gap:15px}
    .two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}.field-action{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:end}.hint{margin-top:6px;color:var(--muted);font-size:13px;line-height:1.4}
    .steps{display:grid;gap:10px}.step{display:grid;grid-template-columns:31px 1fr;gap:10px;padding:12px;background:var(--soft);border:1px solid #e5eaf1;border-radius:7px}.step span{display:grid;place-items:center;width:31px;height:31px;border-radius:50%;background:#dbeafe;color:#1d4ed8;font-weight:800}.step b{display:block;margin-bottom:3px}.step small{display:block;color:var(--muted);font-size:13px;line-height:1.4}
    .logbox{background:#101828;border-radius:7px;border:1px solid #1f2937;overflow:hidden}.loghead{display:flex;justify-content:space-between;padding:10px 12px;color:#d0d5dd;border-bottom:1px solid rgba(255,255,255,.09);font-size:13px;font-weight:700}.log{min-height:520px;max-height:calc(100vh - 250px);overflow:auto;white-space:pre-wrap;padding:14px;color:#e5e7eb;font:13px/1.55 Consolas,"Cascadia Mono",monospace}
    @media(max-width:1180px){.workspace{grid-template-columns:1fr}.work-log{position:static}.log{min-height:260px;max-height:420px}}
    @media(max-width:900px){.metrics,.layout,.two,.field-action{grid-template-columns:1fr}.topbar{align-items:flex-start;flex-direction:column}.actions{width:100%}.actions button{flex:1}}
    @media(max-width:540px){.content,.topbar{padding-left:15px;padding-right:15px}.buttons,.actions{display:grid;grid-template-columns:1fr;width:100%}button{width:100%}}
  </style>
</head>
<body>
<div class="shell">
  <aside class="sidebar">
    <div class="brand"><h1>Pixel Drive Capture</h1><p>Chụp ảnh và quay video sản phẩm trực tiếp vào Google Drive đồng bộ.</p></div>
    <div class="nav">
      <div class="active"><span>Bảng điều khiển</span><span>Live</span></div>
      <div><span>Thư mục sản phẩm</span><span id="navFolders">0</span></div>
      <div><span>Google Drive</span><span id="navDrive">...</span></div>
      <div><span>Pixel ADB</span><span id="navAdb">...</span></div>
    </div>
  </aside>
  <main class="main">
    <header class="topbar">
      <div><h2>Trung tâm chụp sản phẩm</h2><p>Chọn thư mục trước, sau đó chụp hoặc quay từ Pixel.</p></div>
      <div class="actions">
        <button class="ghost" onclick="refresh()">Làm mới</button>
        <button class="secondary" onclick="openPreview()">Xem màn hình Pixel</button>
        <button onclick="capture()">Chụp ảnh</button>
        <button onclick="record()">Quay video</button>
      </div>
    </header>
    <div class="content">
      <div class="workspace">
      <div class="work-main">
      <section class="metrics">
        <div class="metric"><small>Pixel ADB</small><strong id="adbMetric"><span class="badge warn">Đang kiểm tra</span></strong></div>
        <div class="metric"><small>Thư mục Drive</small><strong id="driveMetric"><span class="badge warn">Đang kiểm tra</span></strong></div>
        <div class="metric"><small>Thư mục đang chọn</small><strong id="selectedMetric">Chưa chọn</strong></div>
        <div class="metric"><small>Số thư mục sản phẩm</small><strong id="folderMetric">0</strong></div>
        <div class="metric"><small>Trạng thái tác vụ</small><strong id="busyMetric"><span class="badge ok">Sẵn sàng</span></strong></div>
      </section>

      <section class="layout">
        <div class="panel">
          <div class="panel-head"><h3>Thư mục Google Drive</h3><p>App ghi file trực tiếp vào thư mục Google Drive for desktop đang đồng bộ trên máy tính.</p></div>
          <div class="panel-body">
            <div class="field-action">
              <div><label for="driveRoot">Đường dẫn thư mục chính</label><input id="driveRoot" value="G:\My Drive\Test hình ảnh shopee"></div>
              <button onclick="saveDriveRoot()">Lưu và quét lại</button>
            </div>
            <div class="two">
              <div><label for="folderSelect">Chọn thư mục sản phẩm</label><select id="folderSelect" onchange="selectFolder()"><option value="">-- Chưa chọn thư mục --</option></select></div>
              <div><label for="newFolder">Tạo thư mục sản phẩm mới</label><div class="field-action"><input id="newFolder" placeholder="Ví dụ: Eskar Tears 15ml"><button onclick="createFolder()">Tạo</button></div></div>
            </div>
            <div class="buttons"><button class="secondary" onclick="scanFolders()">Quét lại thư mục</button><button class="danger" onclick="deleteFolder()">Xóa thư mục đang chọn</button></div>
            <div class="hint">Bắt buộc chọn đúng thư mục sản phẩm trước khi chụp hoặc quay. App không tự phân loại và không tự tạo album Google Photos.</div>
          </div>
        </div>
        <aside class="panel">
          <div class="panel-head"><h3>Quy trình vận hành</h3><p>Luồng đơn giản, phù hợp xử lý số lượng lớn.</p></div>
          <div class="panel-body steps">
            <div class="step"><span>1</span><div><b>Tạo hoặc chọn thư mục</b><small>Chọn đúng tên sản phẩm trong Drive.</small></div></div>
            <div class="step"><span>2</span><div><b>Điều chỉnh góc máy</b><small>Mở xem màn hình Pixel trước khi thao tác.</small></div></div>
            <div class="step"><span>3</span><div><b>Chụp hoặc quay</b><small>File được chép vào Drive, kiểm tra và xóa khỏi Pixel.</small></div></div>
          </div>
        </aside>
      </section>

      <section class="panel">
        <div class="panel-head"><h3>Điều khiển Pixel</h3><p>Ảnh và video được lưu vào thư mục sản phẩm đang chọn.</p></div>
        <div class="panel-body">
          <div>
            <label for="duration">Thời lượng video (giây)</label>
            <input id="duration" type="number" min="1" max="300" value="10">
            <div class="hint">Giới hạn từ 1 đến 300 giây cho mỗi lần quay.</div>
          </div>
          <div class="buttons">
            <button class="secondary" onclick="openPreview()">Xem màn hình Pixel</button>
            <button onclick="capture()">Chụp ảnh vào thư mục đang chọn</button>
            <button onclick="record()">Quay video vào thư mục đang chọn</button>
          </div>
        </div>
      </section>
      </div>

      <aside class="panel work-log">
        <div class="panel-head"><h3>Nhật ký xử lý</h3><p>Theo dõi từng bước: chụp/quay, kéo file, chép vào Drive và xóa khỏi Pixel.</p></div>
        <div class="panel-body">
          <div class="buttons"><button class="ghost" onclick="clearLog()">Xóa log</button></div>
          <div class="logbox"><div class="loghead"><span>Event stream</span><span id="logCount">0 events</span></div><div id="log" class="log"></div></div>
        </div>
      </aside>
      </div>
    </div>
  </main>
</div>
<script>
  const logBox=document.getElementById("log"); let eventCount=0,lastId=0,poller=null,busy=false;
  function log(v){const t=typeof v==="string"?v:JSON.stringify(v,null,2);eventCount++;document.getElementById("logCount").textContent=`${eventCount} events`;logBox.textContent=`[${new Date().toLocaleTimeString()}]\n${t}\n\n`+logBox.textContent}
  function clearLog(){eventCount=0;lastId=0;logBox.textContent="";document.getElementById("logCount").textContent="0 events"}
  async function api(path,body){const r=await fetch(path,{method:body?"POST":"GET",headers:body?{"Content-Type":"application/json"}:{},body:body?JSON.stringify(body):undefined});const d=await r.json();if(!r.ok)throw d;return d}
  async function pull(){const d=await api(`/api/events?after=${lastId}`);for(const e of d.events||[]){lastId=Math.max(lastId,e.id||0);log(e.payload)}}
  function startPoll(){if(!poller){pull().catch(()=>{});poller=setInterval(()=>pull().catch(()=>{}),700)}}
  async function stopPoll(){if(poller){clearInterval(poller);poller=null}await pull().catch(()=>{})}
  function selected(){return document.getElementById("folderSelect").value}
  function requireFolder(){if(!selected()){log({error:"Hãy chọn hoặc tạo thư mục sản phẩm trước khi chụp/quay."});return false}return true}
  function setBusy(v){busy=v;document.querySelectorAll("button").forEach(b=>b.disabled=v)}
  function render(d){document.getElementById("adbMetric").innerHTML=d.adb_device?`<span class="badge ok">${d.adb_device}</span>`:`<span class="badge warn">Chưa thấy Pixel</span>`;document.getElementById("driveMetric").innerHTML=d.drive_ready?`<span class="badge ok">Đã kết nối</span>`:`<span class="badge warn">Không tìm thấy</span>`;document.getElementById("selectedMetric").textContent=d.selected_folder||"Chưa chọn";document.getElementById("folderMetric").textContent=(d.folders||[]).length;document.getElementById("busyMetric").innerHTML=d.operation_busy?'<span class="badge warn">Đang xử lý</span>':'<span class="badge ok">Sẵn sàng</span>';document.getElementById("navFolders").textContent=(d.folders||[]).length;document.getElementById("navDrive").textContent=d.drive_ready?"OK":"Lỗi";document.getElementById("navAdb").textContent=d.adb_device?"OK":"Offline";document.getElementById("driveRoot").value=d.drive_root;const s=document.getElementById("folderSelect"),current=d.selected_folder||s.value;s.innerHTML='<option value="">-- Chưa chọn thư mục --</option>'+d.folders.map(f=>`<option value="${escapeHtml(f)}">${escapeHtml(f)}</option>`).join("");s.value=current}
  function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
  async function refresh(){try{render(await api("/api/status"))}catch(e){log(e)}}
  async function scanFolders(){try{render(await api("/api/status"));log({status:"Đã quét lại danh sách thư mục."})}catch(e){log(e)}}
  async function saveDriveRoot(){try{log(await api("/api/drive-root",{drive_root:document.getElementById("driveRoot").value}));await refresh()}catch(e){log(e)}}
  async function createFolder(){try{const d=await api("/api/folders",{name:document.getElementById("newFolder").value});document.getElementById("newFolder").value="";log(d);await refresh()}catch(e){log(e)}}
  async function deleteFolder(){const name=selected();if(!name){log({error:"Hãy chọn thư mục cần xóa."});return}if(!confirm(`Xóa thư mục rỗng "${name}"?`))return;try{log(await api("/api/folders/delete",{name}));await refresh()}catch(e){log(e)}}
  async function selectFolder(){try{const d=await api("/api/select-folder",{name:selected()});log(d);await refresh()}catch(e){log(e)}}
  async function openPreview(){try{log(await api("/api/open-preview",{}))}catch(e){log(e)}}
  async function run(path,body){if(!requireFolder()||busy)return;setBusy(true);await api("/api/events/clear",{}).catch(()=>{});lastId=0;startPoll();try{log(await api(path,body));await refresh()}catch(e){log(e)}finally{await stopPoll();setBusy(false)}}
  function capture(){run("/api/capture",{folder:selected()})}
  function record(){run("/api/record",{folder:selected(),duration:Number(document.getElementById("duration").value||10)})}
  refresh();
</script>
</body>
</html>
"""


def settings() -> pipeline.Settings:
    pipeline.load_dotenv(ROOT)
    return pipeline.load_settings(CONFIG_PATH)


def load_config() -> dict[str, Any]:
    with CONFIG_LOCK:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config: dict[str, Any]) -> None:
    with CONFIG_LOCK:
        temp_path = CONFIG_PATH.with_suffix(".json.tmp")
        temp_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(temp_path, CONFIG_PATH)


def drive_root() -> Path:
    config = load_config()
    value = config.get("paths", {}).get("drive_root_dir", DEFAULT_DRIVE_ROOT)
    return Path(value).expanduser()


def selected_folder_name() -> str:
    return str(load_config().get("paths", {}).get("selected_drive_folder", "")).strip()


def save_path_setting(key: str, value: str) -> None:
    with CONFIG_LOCK:
        config = load_config()
        config.setdefault("paths", {})[key] = value
        save_config(config)


def validate_drive_root(path: Path) -> Path:
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Không tìm thấy thư mục Drive: {path}")
    return path.resolve()


def list_drive_folders() -> list[str]:
    root = validate_drive_root(drive_root())
    return sorted((path.name for path in root.iterdir() if path.is_dir()), key=str.casefold)


def validate_folder_name(name: str) -> str:
    cleaned = name.strip().rstrip(". ")
    if not cleaned:
        raise ValueError("Tên thư mục sản phẩm không được để trống.")
    if any(char in cleaned for char in '<>:"/\\|?*'):
        raise ValueError("Tên thư mục chứa ký tự không hợp lệ trên Windows.")
    if cleaned in {".", ".."}:
        raise ValueError("Tên thư mục không hợp lệ.")
    return cleaned


def selected_drive_folder(requested: str | None = None) -> Path:
    root = validate_drive_root(drive_root())
    name = validate_folder_name((requested or selected_folder_name()).strip())
    target = (root / name).resolve()
    if target.parent != root or not target.is_dir():
        raise ValueError("Thư mục sản phẩm không tồn tại. Hãy quét lại và chọn đúng thư mục.")
    return target


def unique_target(folder: Path, filename: str) -> Path:
    candidate = folder / filename
    if not candidate.exists():
        return candidate
    stem, suffix = Path(filename).stem, Path(filename).suffix
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for index in range(1, 1000):
        candidate = folder / f"{stem}_{stamp}_{index:03d}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Không thể tạo tên file duy nhất trong thư mục Drive.")


def copy_media_to_drive(source: Path, folder: Path) -> Path:
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"Không tìm thấy file vừa kéo từ Pixel: {source}")
    target = unique_target(folder, source.name)
    temp = target.with_name(f".{target.name}.part")
    target_created = False
    try:
        shutil.copy2(source, temp)
        if temp.stat().st_size != source.stat().st_size:
            raise RuntimeError("File chép vào Drive không đủ dung lượng. App giữ nguyên file trên Pixel.")
        os.replace(temp, target)
        target_created = True
        if target.stat().st_size != source.stat().st_size:
            raise RuntimeError("Không xác minh được file đích trong Drive. App giữ nguyên file trên Pixel.")
    except Exception:
        temp.unlink(missing_ok=True)
        if target_created:
            target.unlink(missing_ok=True)
        raise
    return target


def finalize_pixel_media(cfg: pipeline.Settings, local_path: Path) -> dict[str, str]:
    try:
        remote = pipeline.delete_pixel_media(cfg, local_path)
        local_path.unlink(missing_ok=True)
        return {"pixel_file": remote, "cleanup": "Đã xóa file khỏi Pixel sau khi chép Drive thành công."}
    except Exception as exc:
        return {"cleanup_warning": f"File đã có trong Drive nhưng chưa xóa được khỏi Pixel: {exc}"}


def add_event(payload: dict[str, Any]) -> None:
    global EVENT_COUNTER
    with EVENT_LOCK:
        EVENT_COUNTER += 1
        EVENTS.append({"id": EVENT_COUNTER, "payload": payload})
        del EVENTS[:-200]


def error_response(exc: Exception, status: int = 500):
    return jsonify({"error": str(exc)}), status


def adb_device_serial(cfg: pipeline.Settings) -> str:
    if cfg.adb_serial:
        return cfg.adb_serial
    output = pipeline.adb_command(cfg, "devices", check=False).stdout.splitlines()
    devices = [line.split()[0] for line in output if "\tdevice" in line]
    if not devices:
        raise RuntimeError("Chưa thấy Pixel qua ADB. Kiểm tra cáp USB và USB debugging.")
    if len(devices) > 1:
        raise RuntimeError("Có nhiều thiết bị ADB. Điền adb_serial trong config.json.")
    return devices[0]


def find_scrcpy_exe() -> Path:
    configured = os.environ.get("SCRCPY_PATH", "").strip()
    candidates = [
        Path(configured) if configured else None,
        Path(r"C:\FastbootFirmwareFlasher\ExtraTools\scrcpy\scrcpy.exe"),
    ]
    found = shutil.which("scrcpy")
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    raise FileNotFoundError("Không tìm thấy scrcpy.exe. Cài scrcpy hoặc set SCRCPY_PATH trong .env.")


def open_camera(cfg: pipeline.Settings) -> None:
    pipeline.adb_command(cfg, "shell", "am", "start", "-a", "android.media.action.STILL_IMAGE_CAMERA", check=False)


def stop_existing_scrcpy() -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/IM", "scrcpy.exe", "/F"], text=True, capture_output=True, check=False)


def running_scrcpy_processes() -> list[str]:
    if os.name != "nt":
        return []
    command = "Get-Process scrcpy -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"
    output = subprocess.run(["powershell", "-NoProfile", "-Command", command], text=True, capture_output=True, check=False).stdout
    return [line.strip() for line in output.splitlines() if line.strip()]


@app.get("/")
def index():
    return render_template_string(HTML)


@app.get("/api/events")
def api_events():
    after = int(request.args.get("after") or 0)
    with EVENT_LOCK:
        return jsonify({"events": [event for event in EVENTS if int(event["id"]) > after]})


@app.post("/api/events/clear")
def api_clear_events():
    global EVENT_COUNTER
    with EVENT_LOCK:
        EVENTS.clear()
        EVENT_COUNTER = 0
    return jsonify({"status": "Đã xóa log."})


@app.get("/api/status")
def api_status():
    cfg = settings()
    adb = pipeline.adb_command(cfg, "devices", check=False).stdout.splitlines()
    devices = [line.split()[0] for line in adb if "\tdevice" in line]
    try:
        folders, ready = list_drive_folders(), True
    except Exception:
        folders, ready = [], False
    return jsonify({"adb_device": devices[0] if devices else "", "drive_root": str(drive_root()), "drive_ready": ready, "selected_folder": selected_folder_name(), "folders": folders, "operation_busy": OPERATION_LOCK.locked()})


@app.post("/api/drive-root")
def api_drive_root():
    try:
        value = str((request.json or {}).get("drive_root", "")).strip()
        root = validate_drive_root(Path(value).expanduser())
        save_path_setting("drive_root_dir", str(root))
        save_path_setting("selected_drive_folder", "")
        return jsonify({"status": "Đã lưu thư mục Drive.", "drive_root": str(root), "folders": list_drive_folders()})
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/folders")
def api_create_folder():
    try:
        root = validate_drive_root(drive_root())
        name = validate_folder_name(str((request.json or {}).get("name", "")))
        target = root / name
        created = not target.exists()
        target.mkdir(exist_ok=True)
        if not target.is_dir():
            raise ValueError("Đường dẫn đã tồn tại nhưng không phải thư mục.")
        save_path_setting("selected_drive_folder", name)
        return jsonify({"status": "Đã tạo thư mục." if created else "Thư mục đã tồn tại, app đã chọn lại.", "folder": name, "path": str(target)})
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/select-folder")
def api_select_folder():
    try:
        name = str((request.json or {}).get("name", "")).strip()
        target = selected_drive_folder(name)
        save_path_setting("selected_drive_folder", target.name)
        return jsonify({"status": "Đã chọn thư mục sản phẩm.", "folder": target.name, "path": str(target)})
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/folders/delete")
def api_delete_folder():
    try:
        if OPERATION_LOCK.locked():
            raise RuntimeError("Pixel đang chụp hoặc quay. Hãy đợi tác vụ hiện tại hoàn tất.")
        name = str((request.json or {}).get("name", "")).strip()
        target = selected_drive_folder(name)
        if any(target.iterdir()):
            raise ValueError("Thư mục không rỗng. Hãy kiểm tra và di chuyển hoặc xóa file bên trong trước.")
        target.rmdir()
        if selected_folder_name() == target.name:
            save_path_setting("selected_drive_folder", "")
        add_event({"step": "folder_deleted", "message": "Đã xóa thư mục rỗng.", "folder": target.name})
        return jsonify({"status": "Đã xóa thư mục rỗng.", "folder": target.name})
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/open-preview")
def api_open_preview():
    try:
        if OPERATION_LOCK.locked():
            raise RuntimeError("Pixel đang chụp hoặc quay. Hãy đợi tác vụ hiện tại hoàn tất.")
        cfg, scrcpy = settings(), find_scrcpy_exe()
        serial = adb_device_serial(cfg)
        stop_existing_scrcpy()
        open_camera(cfg)
        time.sleep(0.8)
        args = [str(scrcpy), "--serial", serial, "--stay-awake", "--no-audio", "--window-title", "Pixel Drive Capture - Camera Preview"]
        env = os.environ.copy()
        adb = os.environ.get("ADB", "").strip() or shutil.which("adb")
        if adb:
            env["ADB"] = adb
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        subprocess.Popen(args, cwd=str(scrcpy.parent), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
        time.sleep(2)
        pids = running_scrcpy_processes()
        if os.name == "nt" and not pids:
            raise RuntimeError("scrcpy đã thoát ngay. Hãy kiểm tra ADB/driver.")
        return jsonify({"status": "Đã mở màn hình Pixel.", "adb_serial": serial, "scrcpy_pids": pids})
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/capture")
def api_capture():
    if not OPERATION_LOCK.acquire(blocking=False):
        return error_response(RuntimeError("Pixel đang xử lý một tác vụ khác. Hãy đợi hoàn tất rồi thử lại."), 409)
    try:
        cfg = settings()
        folder = selected_drive_folder(str((request.json or {}).get("folder", "")).strip())
        add_event({"step": "capture", "message": "Đang mở camera Pixel và chụp ảnh.", "folder": folder.name})
        media = pipeline.capture_from_pixel(cfg)
        add_event({"step": "pulled", "message": "Đã kéo ảnh mới từ Pixel về máy.", "file": str(media)})
        target = copy_media_to_drive(media, folder)
        add_event({"step": "drive_saved", "message": "Đã chép ảnh vào thư mục Drive.", "file": str(target), "size": target.stat().st_size})
        cleanup = finalize_pixel_media(cfg, media)
        add_event({"step": "cleanup", **cleanup})
        payload = {"status": "Hoàn tất chụp ảnh.", "drive_file": str(target), "folder": folder.name, **cleanup}
        add_event({"step": "done", **payload})
        return jsonify(payload)
    except Exception as exc:
        add_event({"step": "error", "message": str(exc)})
        return error_response(exc)
    finally:
        OPERATION_LOCK.release()


@app.post("/api/record")
def api_record():
    if not OPERATION_LOCK.acquire(blocking=False):
        return error_response(RuntimeError("Pixel đang xử lý một tác vụ khác. Hãy đợi hoàn tất rồi thử lại."), 409)
    try:
        cfg = settings()
        payload = request.json or {}
        folder = selected_drive_folder(str(payload.get("folder", "")).strip())
        duration = max(1, min(int(payload.get("duration") or 10), 300))
        add_event({"step": "record", "message": "Đang quay video trên Pixel.", "folder": folder.name, "duration": duration})
        media = pipeline.capture_video_from_pixel(cfg, duration)
        add_event({"step": "pulled", "message": "Đã kéo video mới từ Pixel về máy.", "file": str(media)})
        target = copy_media_to_drive(media, folder)
        add_event({"step": "drive_saved", "message": "Đã chép video vào thư mục Drive.", "file": str(target), "size": target.stat().st_size})
        cleanup = finalize_pixel_media(cfg, media)
        add_event({"step": "cleanup", **cleanup})
        result = {"status": "Hoàn tất quay video.", "drive_file": str(target), "folder": folder.name, "duration": duration, **cleanup}
        add_event({"step": "done", **result})
        return jsonify(result)
    except Exception as exc:
        add_event({"step": "error", "message": str(exc)})
        return error_response(exc)
    finally:
        OPERATION_LOCK.release()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8765")), debug=False, threaded=True)
