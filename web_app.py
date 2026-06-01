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
  <title>Pixel Product Agent</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f3f5f7;
      --panel: #ffffff;
      --panel-soft: #f8fafc;
      --text: #172033;
      --muted: #64748b;
      --line: #d8dee8;
      --line-strong: #b9c2d0;
      --brand: #155eef;
      --brand-strong: #0f47c5;
      --ok-bg: #eaf7ef;
      --ok: #137333;
      --warn-bg: #fff6e5;
      --warn: #a15c00;
      --dark: #101828;
      --shadow: 0 10px 30px rgba(16, 24, 40, 0.08);
      font-family: Inter, "Segoe UI", Arial, sans-serif;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--bg); color: var(--text); }
    button, input, select { font: inherit; }
    button {
      min-height: 40px;
      border: 0;
      border-radius: 7px;
      padding: 10px 14px;
      background: var(--brand);
      color: #ffffff;
      cursor: pointer;
      font-weight: 700;
      white-space: nowrap;
    }
    button:hover { background: var(--brand-strong); }
    button.secondary { background: #455468; }
    button.secondary:hover { background: #344054; }
    button.ghost { background: #eef2f7; color: #243041; }
    button.ghost:hover { background: #e2e8f0; }
    button:disabled { opacity: .56; cursor: wait; }
    input, select {
      width: 100%;
      min-height: 42px;
      border: 1px solid var(--line-strong);
      border-radius: 7px;
      background: #ffffff;
      padding: 10px 12px;
      color: var(--text);
      outline: none;
    }
    input:focus, select:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px rgba(21, 94, 239, .12);
    }
    label { display: block; margin-bottom: 7px; color: #1f2937; font-weight: 700; }
    .app-shell { min-height: 100vh; display: grid; grid-template-columns: 248px minmax(0, 1fr); }
    .sidebar {
      background: #0f172a;
      color: #e5e7eb;
      padding: 20px 18px;
      position: sticky;
      top: 0;
      height: 100vh;
    }
    .brand { display: grid; gap: 4px; padding-bottom: 22px; border-bottom: 1px solid rgba(255,255,255,.12); }
    .brand-title { font-size: 18px; font-weight: 800; letter-spacing: 0; }
    .brand-subtitle { color: #a9b4c7; font-size: 13px; line-height: 1.4; }
    .nav { display: grid; gap: 6px; margin-top: 22px; }
    .nav-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 10px 11px;
      border-radius: 7px;
      color: #cbd5e1;
      font-size: 14px;
    }
    .nav-item.active { background: rgba(255,255,255,.10); color: #ffffff; }
    .main { min-width: 0; }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      padding: 18px 26px;
      background: rgba(255,255,255,.86);
      border-bottom: 1px solid var(--line);
      position: sticky;
      top: 0;
      z-index: 5;
      backdrop-filter: blur(10px);
    }
    .topbar h1 { margin: 0; font-size: 22px; line-height: 1.15; }
    .topbar p { margin: 4px 0 0; color: var(--muted); font-size: 14px; }
    .top-actions { display: flex; align-items: center; gap: 10px; }
    .content { max-width: 1220px; margin: 0 auto; padding: 24px 26px 38px; display: grid; gap: 18px; }
    .status-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
    .status-grid.five { grid-template-columns: repeat(5, minmax(0, 1fr)); }
    .status-grid.six { grid-template-columns: repeat(6, minmax(0, 1fr)); }
    .status-grid.seven { grid-template-columns: repeat(7, minmax(0, 1fr)); }
    .metric {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 15px;
      box-shadow: var(--shadow);
      min-height: 94px;
    }
    .metric-label { color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }
    .metric-value { margin-top: 8px; font-size: 18px; font-weight: 800; overflow-wrap: anywhere; }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 13px;
      font-weight: 700;
    }
    .badge.ok { background: var(--ok-bg); color: var(--ok); }
    .badge.warn { background: var(--warn-bg); color: var(--warn); }
    .layout { display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(340px, .75fr); gap: 18px; align-items: start; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .panel-header {
      padding: 16px 18px;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      gap: 14px;
      align-items: start;
    }
    .panel-title { margin: 0; font-size: 17px; }
    .panel-subtitle { margin: 4px 0 0; color: var(--muted); font-size: 13px; line-height: 1.45; }
    .panel-body { padding: 18px; display: grid; gap: 16px; }
    .field-row { display: grid; grid-template-columns: minmax(0, 1fr) 132px; gap: 10px; align-items: start; }
    .field-row button { margin-top: 29px; width: 132px; }
    .two-col { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .button-row { display: flex; flex-wrap: wrap; gap: 10px; }
    .test-tools {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 12px;
      background: var(--panel-soft);
      border: 1px solid #e5eaf1;
      border-radius: 8px;
    }
    .hint { color: var(--muted); font-size: 13px; line-height: 1.45; margin-top: 7px; }
    .steps { display: grid; gap: 10px; }
    .step {
      display: grid;
      grid-template-columns: 32px minmax(0, 1fr);
      gap: 11px;
      padding: 12px;
      background: var(--panel-soft);
      border: 1px solid #e5eaf1;
      border-radius: 8px;
    }
    .step-num {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: #dbeafe;
      color: #1d4ed8;
      font-weight: 800;
    }
    .step-title { font-weight: 800; margin-bottom: 2px; }
    .step-text { color: var(--muted); font-size: 13px; line-height: 1.45; }
    .products {
      min-height: 90px;
      display: flex;
      align-content: flex-start;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 8px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      min-height: 28px;
      background: #eef2ff;
      color: #3730a3;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 13px;
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .empty { color: var(--muted); font-size: 14px; padding: 8px 0; }
    .log-wrap { background: var(--dark); border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; }
    .log-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      padding: 10px 12px;
      border-bottom: 1px solid rgba(255,255,255,.08);
      color: #d0d5dd;
      font-size: 13px;
      font-weight: 700;
    }
    .status {
      white-space: pre-wrap;
      color: #e5e7eb;
      padding: 14px;
      min-height: 240px;
      max-height: 460px;
      overflow: auto;
      font: 13px/1.55 Consolas, "Cascadia Mono", monospace;
    }
    @media (max-width: 980px) {
      .app-shell { grid-template-columns: 1fr; }
      .sidebar { position: static; height: auto; }
      .status-grid, .status-grid.five, .status-grid.six, .status-grid.seven, .layout, .two-col, .field-row { grid-template-columns: 1fr; }
      .field-row button { margin-top: 0; width: 100%; }
      .topbar { align-items: flex-start; flex-direction: column; }
      .top-actions { width: 100%; }
      .top-actions button { flex: 1; }
    }
    @media (max-width: 560px) {
      .content, .topbar { padding-left: 16px; padding-right: 16px; }
      .button-row, .top-actions { display: grid; grid-template-columns: 1fr; width: 100%; }
      button { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-title">Pixel Product Agent</div>
        <div class="brand-subtitle">T&#7921; &#273;&#7897;ng ch&#7909;p, nh&#7853;n di&#7879;n v&#224; l&#432;u &#7843;nh s&#7843;n ph&#7849;m.</div>
      </div>
      <nav class="nav" aria-label="Main">
        <div class="nav-item active"><span>B&#7843;ng &#273;i&#7873;u khi&#7875;n</span><span>Live</span></div>
        <div class="nav-item"><span>D&#7919; li&#7879;u s&#7843;n ph&#7849;m</span><span id="navProductCount">0</span></div>
        <div class="nav-item"><span>Google Photos</span><span id="navGoogle">...</span></div>
        <div class="nav-item"><span>Pixel ADB</span><span id="navAdb">...</span></div>
      </nav>
    </aside>

    <div class="main">
      <header class="topbar">
        <div>
          <h1>Trung t&#226;m ch&#7909;p &#7843;nh s&#7843;n ph&#7849;m</h1>
          <p>Qu&#7843;n l&#253; catalog, &#273;i&#7873;u khi&#7875;n Pixel v&#224; upload Google Photos t&#7915; m&#7897;t giao di&#7879;n.</p>
        </div>
        <div class="top-actions">
          <button class="ghost" onclick="refresh()">L&#224;m m&#7899;i</button>
          <button id="topCaptureBtn" onclick="captureUpload()">Ch&#7909;p &#7843;nh</button>
          <button id="topRecordBtn" onclick="recordUpload()">Quay video</button>
        </div>
      </header>

      <main class="content">
        <section class="status-grid seven" aria-label="System status">
          <div class="metric">
            <div class="metric-label">Pixel ADB</div>
            <div id="adbMetric" class="metric-value"><span class="badge warn">Dang kiem tra</span></div>
          </div>
          <div class="metric">
            <div class="metric-label">Google token</div>
            <div id="googleMetric" class="metric-value"><span class="badge warn">Dang kiem tra</span></div>
          </div>
          <div class="metric">
            <div class="metric-label">AI provider</div>
            <div id="aiMetric" class="metric-value">...</div>
          </div>
          <div class="metric">
            <div class="metric-label">GPT API</div>
            <div id="gptMetric" class="metric-value"><span class="badge warn">Chưa kiểm tra</span></div>
          </div>
          <div class="metric">
            <div class="metric-label">Gemini API</div>
            <div id="geminiMetric" class="metric-value"><span class="badge warn">Chưa kiểm tra</span></div>
          </div>
          <div class="metric">
            <div class="metric-label">Web Search</div>
            <div id="searchMetric" class="metric-value"><span class="badge warn">Chưa kiểm tra</span></div>
          </div>
          <div class="metric">
            <div class="metric-label">S&#7843;n ph&#7849;m &#273;&#227; n&#7841;p</div>
            <div id="productMetric" class="metric-value">0</div>
          </div>
        </section>

        <section class="layout">
          <div class="panel">
            <div class="panel-header">
              <div>
                <h2 class="panel-title">N&#7841;p d&#7919; li&#7879;u s&#7843;n ph&#7849;m</h2>
                <p class="panel-subtitle">Ch&#7885;n th&#432; m&#7909;c ch&#7913;a &#7843;nh m&#7857;t tr&#432;&#7899;c, m&#7857;t sau, barcode v&#224; t&#224;i li&#7879;u t&#234;n s&#7843;n ph&#7849;m.</p>
              </div>
            </div>
            <div class="panel-body">
              <div class="field-row">
                <div>
                  <label for="sourcePath">&#272;&#432;&#7901;ng d&#7851;n th&#432; m&#7909;c</label>
                  <input id="sourcePath" placeholder="V&#237; d&#7909;: D:\product-data">
                  <div class="hint">M&#7895;i s&#7843;n ph&#7849;m n&#234;n l&#224; m&#7897;t th&#432; m&#7909;c ri&#234;ng. File .txt/.csv/.json/.docx/.pdf c&#243; th&#7875; ch&#7913;a t&#234;n s&#7843;n ph&#7849;m m&#7895;i d&#242;ng.</div>
                </div>
                <button id="ingestBtn" onclick="ingest()">Qu&#233;t d&#7919; li&#7879;u</button>
              </div>
            <div class="button-row">
              <button class="secondary" onclick="resetCatalog()">X&#243;a catalog v&#224; qu&#233;t l&#7841;i</button>
              <button class="ghost" onclick="resetAlbumCache()">X&#243;a cache album Google Photos</button>
            </div>
            </div>
          </div>

          <aside class="panel">
            <div class="panel-header">
              <div>
                <h2 class="panel-title">Quy tr&#236;nh v&#7853;n h&#224;nh</h2>
                <p class="panel-subtitle">D&#7919; li&#7879;u c&#224;ng r&#245;, AI c&#224;ng &#237;t nh&#7847;m album.</p>
              </div>
            </div>
            <div class="panel-body steps">
              <div class="step">
                <div class="step-num">1</div>
                <div><div class="step-title">N&#7841;p catalog</div><div class="step-text">Qu&#233;t th&#432; m&#7909;c s&#7843;n ph&#7849;m v&#224; &#7843;nh m&#7851;u.</div></div>
              </div>
              <div class="step">
                <div class="step-num">2</div>
                <div><div class="step-title">Ch&#7909;p ho&#7863;c quay t&#7915; Pixel</div><div class="step-text">ADB m&#7903; camera, t&#7841;o media v&#224; k&#233;o file v&#7873; m&#225;y.</div></div>
              </div>
              <div class="step">
                <div class="step-num">3</div>
                <div><div class="step-title">AI ph&#226;n lo&#7841;i</div><div class="step-text">H&#7879; th&#7889;ng ch&#7885;n s&#7843;n ph&#7849;m, t&#7841;o album v&#224; upload Google Photos.</div></div>
              </div>
            </div>
          </aside>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2 class="panel-title">Ch&#7909;p / quay v&#224; upload</h2>
              <p class="panel-subtitle">&#272;&#7875; tr&#7889;ng t&#234;n s&#7843;n ph&#7849;m n&#7871;u mu&#7889;n AI t&#7921; nh&#7853;n di&#7879;n. Khi quay video, h&#7879; th&#7889;ng ch&#7909;p &#7843;nh tham chi&#7871;u tr&#432;&#7899;c &#273;&#7875; ph&#226;n lo&#7841;i album.</p>
            </div>
          </div>
          <div class="panel-body">
            <div class="two-col">
              <div>
                <label for="provider">AI provider</label>
                <select id="provider">
                  <option value="both">OpenAI + Gemini</option>
                  <option value="openai">OpenAI</option>
                  <option value="gemini">Gemini</option>
                  <option value="offline">Offline m&#7851;u &#7843;nh</option>
                </select>
              </div>
              <div>
                <label for="forcedProduct">&#201;p t&#234;n s&#7843;n ph&#7849;m khi test</label>
                <input id="forcedProduct" placeholder="&#272;&#7875; tr&#7889;ng &#273;&#7875; AI t&#7921; nh&#7853;n di&#7879;n">
              </div>
            </div>
            <div>
              <label for="videoDuration">Th&#7901;i l&#432;&#7907;ng video (gi&#226;y)</label>
              <input id="videoDuration" type="number" min="1" max="300" value="10">
              <div class="hint">Gi&#7899;i h&#7841;n t&#7915; 1 &#273;&#7871;n 300 gi&#226;y cho m&#7895;i l&#7847;n quay.</div>
            </div>
            <div class="button-row">
              <button id="captureBtn" onclick="captureUpload()">Ch&#7909;p &#7843;nh t&#7915; Pixel v&#224; upload</button>
              <button id="recordBtn" onclick="recordUpload()">Quay video t&#7915; Pixel v&#224; upload</button>
            </div>
            <div class="test-tools">
              <div>
                <div class="step-title">Ki&#7875;m th&#7917; AI</div>
                <div class="step-text">Ch&#7841;y nh&#7853;n di&#7879;n tr&#234;n &#7843;nh m&#7899;i nh&#7845;t trong inbox, kh&#244;ng ch&#7909;p m&#7899;i v&#224; kh&#244;ng upload.</div>
              </div>
              <button class="ghost" onclick="classifyLatest()">Test nh&#7853;n di&#7879;n &#7843;nh m&#7899;i nh&#7845;t</button>
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2 class="panel-title">C&#7845;u h&#236;nh API AI</h2>
              <p class="panel-subtitle">Nh&#7853;p OpenAI API key m&#7899;i khi key c&#361; h&#7871;t h&#7841;n, b&#7883; revoke ho&#7863;c kh&#244;ng c&#242;n quota. Key &#273;&#432;&#7907;c l&#432;u c&#7909;c b&#7897; trong file .env v&#224; kh&#244;ng hi&#7875;n th&#7883; l&#7841;i tr&#234;n giao di&#7879;n.</p>
            </div>
          </div>
          <div class="panel-body">
            <div class="field-row">
              <div>
                <label for="openaiApiKey">OpenAI API key</label>
                <input id="openaiApiKey" type="password" autocomplete="off" placeholder="sk-... ho&#7863;c sk-proj-...">
                <div id="apiKeyStatus" class="hint">Tr&#7841;ng th&#225;i key: &#273;ang ki&#7875;m tra...</div>
              </div>
              <button id="saveOpenAiKeyBtn" onclick="saveOpenAiKey()">L&#432;u server</button>
            </div>
            <div class="button-row">
              <button class="ghost" onclick="saveOpenAiKeyToBrowser()">L&#432;u t&#7841;i tr&#236;nh duy&#7879;t</button>
              <button class="secondary" onclick="checkGptApi()">Ki&#7875;m tra GPT API</button>
            </div>
            <div class="field-row">
              <div>
                <label for="geminiApiKey">Gemini API key</label>
                <input id="geminiApiKey" type="password" autocomplete="off" placeholder="AIza...">
                <div id="geminiKeyStatus" class="hint">Tr&#7841;ng th&#225;i key Gemini: &#273;ang ki&#7875;m tra...</div>
              </div>
              <button id="saveGeminiKeyBtn" onclick="saveGeminiKey()">L&#432;u server</button>
            </div>
            <div class="button-row">
              <button class="ghost" onclick="saveGeminiKeyToBrowser()">L&#432;u t&#7841;i tr&#236;nh duy&#7879;t</button>
              <button class="secondary" onclick="checkGeminiApi()">Ki&#7875;m tra Gemini API</button>
            </div>
            <div class="hint">L&#432;u server ghi key v&#224;o file .env &#273;&#7875; app d&#249;ng khi ch&#7909;p/quay. L&#432;u t&#7841;i tr&#236;nh duy&#7879;t ch&#7881; gi&#7919; key trong browser &#273;&#7875; t&#7921; &#273;i&#7873;n l&#7841;i.</div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2 class="panel-title">T&#236;m s&#7843;n ph&#7849;m tr&#234;n internet</h2>
              <p class="panel-subtitle">Khi catalog kh&#244;ng nh&#7853;n ra s&#7843;n ph&#7849;m, agent s&#7869; d&#249;ng OpenAI/Gemini &#273;&#7885;c &#7843;nh, t&#7841;o truy v&#7845;n, t&#236;m h&#236;nh &#7843;nh web, &#273;&#7889;i chi&#7871;u v&#224; ch&#7881; t&#7921; t&#7841;o album khi &#273;&#7911; tin c&#7853;y.</p>
            </div>
          </div>
          <div class="panel-body">
            <div class="two-col">
              <div>
                <label for="searchProvider">Search provider</label>
                <select id="searchProvider">
                  <option value="serpapi">SerpAPI Google Images</option>
                  <option value="google_cse">Google Custom Search</option>
                  <option value="bing">Bing Image Search</option>
                </select>
              </div>
              <div>
                <label for="searchApiKey">Search API key</label>
                <input id="searchApiKey" type="password" autocomplete="off" placeholder="SerpAPI / Google CSE / Bing key">
              </div>
            </div>
            <div class="two-col">
              <div>
                <label for="googleCseCx">Google CSE CX</label>
                <input id="googleCseCx" autocomplete="off" placeholder="Ch&#7881; c&#7847;n khi d&#249;ng Google Custom Search">
              </div>
              <div>
                <label for="webConfidenceThreshold">Ng&#432;&#7905;ng t&#7921; t&#7841;o album</label>
                <input id="webConfidenceThreshold" type="number" min="0" max="1" step="0.01" value="0.78">
              </div>
            </div>
            <div class="button-row">
              <button id="saveSearchSettingsBtn" onclick="saveSearchSettings()">L&#432;u c&#7845;u h&#236;nh t&#236;m web</button>
              <button class="secondary" onclick="checkSearchApi()">Ki&#7875;m tra Search API</button>
            </div>
            <div id="searchKeyStatus" class="hint">N&#7871;u ch&#432;a nh&#7853;p Search API key, enrichment s&#7869; t&#7921; b&#7887; qua v&#224; h&#7879; th&#7889;ng v&#7851;n ho&#7841;t &#273;&#7897;ng theo catalog hi&#7879;n c&#243;.</div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2 class="panel-title">S&#7843;n ph&#7849;m &#273;&#227; n&#7841;p</h2>
              <p class="panel-subtitle">Danh s&#225;ch n&#224;y l&#224; t&#7853;p t&#234;n m&#224; AI &#273;&#432;&#7907;c ph&#233;p ch&#7885;n khi upload.</p>
            </div>
          </div>
          <div class="panel-body">
            <div id="products" class="products"></div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <div>
              <h2 class="panel-title">Nh&#7853;t k&#253; x&#7917; l&#253;</h2>
              <p class="panel-subtitle">Hi&#7875;n th&#7883; k&#7871;t qu&#7843; qu&#233;t catalog, nh&#7853;n di&#7879;n v&#224; upload.</p>
            </div>
            <button class="ghost" onclick="clearLog()">X&#243;a log</button>
          </div>
          <div class="panel-body">
            <div class="log-wrap">
              <div class="log-head"><span>Event stream</span><span id="logCount">0 events</span></div>
              <div id="log" class="status"></div>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>

  <script>
    const logBox = document.getElementById("log");
    let eventCount = 0;

    function log(value) {
      const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
      const time = new Date().toLocaleTimeString();
      eventCount += 1;
      document.getElementById("logCount").textContent = `${eventCount} events`;
      logBox.textContent = `[${time}]\n${text}\n\n` + logBox.textContent;
    }

    function clearLog() {
      eventCount = 0;
      document.getElementById("logCount").textContent = "0 events";
      logBox.textContent = "";
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

    function setBusy(isBusy) {
      document.getElementById("ingestBtn").disabled = isBusy;
      document.getElementById("captureBtn").disabled = isBusy;
      document.getElementById("recordBtn").disabled = isBusy;
      document.getElementById("topCaptureBtn").disabled = isBusy;
      document.getElementById("topRecordBtn").disabled = isBusy;
    }

    function renderStatus(data) {
      const hasAdb = Boolean(data.adb_device);
      const hasGoogle = Boolean(data.google_token);
      const products = data.products || [];

      document.getElementById("adbMetric").innerHTML = hasAdb
        ? `<span class="badge ok">${data.adb_device}</span>`
        : `<span class="badge warn">Chưa thấy Pixel</span>`;
      document.getElementById("googleMetric").innerHTML = hasGoogle
        ? `<span class="badge ok">Đã kết nối</span>`
        : `<span class="badge warn">Chưa có token</span>`;
      document.getElementById("aiMetric").textContent = data.ai_provider || "...";
      document.getElementById("gptMetric").innerHTML = data.openai_key
        ? `<span class="badge ok">Đã có key</span>`
        : `<span class="badge warn">Thiếu key</span>`;
      document.getElementById("geminiMetric").innerHTML = data.gemini_key
        ? `<span class="badge ok">Đã có key</span>`
        : `<span class="badge warn">Thiếu key</span>`;
      document.getElementById("searchMetric").innerHTML = data.search_key
        ? `<span class="badge ok">${data.search_provider}</span>`
        : `<span class="badge warn">Thiếu key</span>`;
      document.getElementById("apiKeyStatus").textContent = data.openai_key
        ? `Trạng thái key: đã lưu (${data.openai_key_masked})`
        : "Trạng thái key: chưa có OpenAI API key";
      document.getElementById("geminiKeyStatus").textContent = data.gemini_key
        ? "Trạng thái key Gemini: đã lưu"
        : "Trạng thái key Gemini: chưa có Gemini API key";
      document.getElementById("searchProvider").value = data.search_provider || "serpapi";
      document.getElementById("webConfidenceThreshold").value = data.web_confidence_threshold || 0.78;
      document.getElementById("searchKeyStatus").textContent = data.search_key
        ? `Trạng thái search: đã lưu (${data.search_key_masked})`
        : "Trạng thái search: chưa có Search API key";
      document.getElementById("productMetric").textContent = products.filter(p => p !== "Unsorted").length;
      document.getElementById("navProductCount").textContent = products.filter(p => p !== "Unsorted").length;
      document.getElementById("navGoogle").textContent = hasGoogle ? "OK" : "Thiếu";
      document.getElementById("navAdb").textContent = hasAdb ? "OK" : "Offline";
      document.getElementById("provider").value = data.ai_provider;
      document.getElementById("products").innerHTML = products.length
        ? products.map(p => `<span class="pill">${p}</span>`).join("")
        : "<span class='empty'>Chưa có sản phẩm</span>";
    }

    async function refresh() {
      try {
        renderStatus(await api("/api/status"));
      } catch (err) {
        log(err);
      }
    }

    async function ingest() {
      setBusy(true);
      try {
        const data = await api("/api/ingest", {source_path: document.getElementById("sourcePath").value});
        log(data);
        await refresh();
      } catch (err) {
        log(err);
      } finally {
        setBusy(false);
      }
    }

    async function captureUpload() {
      setBusy(true);
      try {
        const data = await api("/api/capture-upload", {
          provider: document.getElementById("provider").value,
          product: document.getElementById("forcedProduct").value
        });
        log(data);
        await refresh();
      } catch (err) {
        log(err);
      } finally {
        setBusy(false);
      }
    }

    async function recordUpload() {
      setBusy(true);
      try {
        const data = await api("/api/record-upload", {
          provider: document.getElementById("provider").value,
          product: document.getElementById("forcedProduct").value,
          duration: Number(document.getElementById("videoDuration").value || 10)
        });
        log(data);
        await refresh();
      } catch (err) {
        log(err);
      } finally {
        setBusy(false);
      }
    }

    async function saveOpenAiKey() {
      const keyInput = document.getElementById("openaiApiKey");
      const apiKey = keyInput.value.trim();
      if (!apiKey) {
        log("Vui lòng nhập OpenAI API key trước khi lưu.");
        return;
      }
      document.getElementById("saveOpenAiKeyBtn").disabled = true;
      try {
        const data = await api("/api/settings/api-key", {provider: "openai", api_key: apiKey});
        keyInput.value = "";
        log(data);
        await refresh();
      } catch (err) {
        log(err);
      } finally {
        document.getElementById("saveOpenAiKeyBtn").disabled = false;
      }
    }

    async function saveGeminiKey() {
      const keyInput = document.getElementById("geminiApiKey");
      const apiKey = keyInput.value.trim();
      if (!apiKey) {
        log("Vui lòng nhập Gemini API key trước khi lưu.");
        return;
      }
      document.getElementById("saveGeminiKeyBtn").disabled = true;
      try {
        const data = await api("/api/settings/api-key", {provider: "gemini", api_key: apiKey});
        keyInput.value = "";
        log(data);
        await refresh();
      } catch (err) {
        log(err);
      } finally {
        document.getElementById("saveGeminiKeyBtn").disabled = false;
      }
    }

    function saveOpenAiKeyToBrowser() {
      const keyInput = document.getElementById("openaiApiKey");
      const apiKey = keyInput.value.trim();
      if (!apiKey) {
        log("Vui lòng nhập OpenAI API key trước khi lưu tại trình duyệt.");
        return;
      }
      localStorage.setItem("pixel_agent_openai_api_key", apiKey);
      log({status: "saved_in_browser", provider: "openai"});
    }

    function saveGeminiKeyToBrowser() {
      const keyInput = document.getElementById("geminiApiKey");
      const apiKey = keyInput.value.trim();
      if (!apiKey) {
        log("Vui lòng nhập Gemini API key trước khi lưu tại trình duyệt.");
        return;
      }
      localStorage.setItem("pixel_agent_gemini_api_key", apiKey);
      log({status: "saved_in_browser", provider: "gemini"});
    }

    async function checkGptApi() {
      const apiKey = document.getElementById("openaiApiKey").value.trim();
      try {
        const data = await api("/api/settings/check-openai", {api_key: apiKey});
        document.getElementById("gptMetric").innerHTML = data.ok
          ? `<span class="badge ok">GPT OK</span>`
          : `<span class="badge warn">${data.status}</span>`;
        log(data);
      } catch (err) {
        document.getElementById("gptMetric").innerHTML = `<span class="badge warn">Lỗi</span>`;
        log(err);
      }
    }

    async function checkGeminiApi() {
      const apiKey = document.getElementById("geminiApiKey").value.trim();
      try {
        const data = await api("/api/settings/check-gemini", {api_key: apiKey});
        document.getElementById("geminiMetric").innerHTML = data.ok
          ? `<span class="badge ok">Gemini OK</span>`
          : `<span class="badge warn">${data.status}</span>`;
        log(data);
      } catch (err) {
        document.getElementById("geminiMetric").innerHTML = `<span class="badge warn">Lỗi</span>`;
        log(err);
      }
    }

    async function saveSearchSettings() {
      const provider = document.getElementById("searchProvider").value;
      const apiKey = document.getElementById("searchApiKey").value.trim();
      const cx = document.getElementById("googleCseCx").value.trim();
      const threshold = Number(document.getElementById("webConfidenceThreshold").value || 0.78);
      document.getElementById("saveSearchSettingsBtn").disabled = true;
      try {
        const data = await api("/api/settings/search", {
          provider,
          api_key: apiKey,
          google_cse_cx: cx,
          confidence_threshold: threshold
        });
        document.getElementById("searchApiKey").value = "";
        log(data);
        await refresh();
      } catch (err) {
        log(err);
      } finally {
        document.getElementById("saveSearchSettingsBtn").disabled = false;
      }
    }

    async function checkSearchApi() {
      const provider = document.getElementById("searchProvider").value;
      try {
        const data = await api("/api/settings/check-search", {provider});
        document.getElementById("searchMetric").innerHTML = data.ok
          ? `<span class="badge ok">Search OK</span>`
          : `<span class="badge warn">${data.status}</span>`;
        log(data);
      } catch (err) {
        document.getElementById("searchMetric").innerHTML = `<span class="badge warn">Lỗi</span>`;
        log(err);
      }
    }

    async function classifyLatest() {
      setBusy(true);
      try {
        log(await api("/api/classify-latest", {provider: document.getElementById("provider").value}));
      } catch (err) {
        log(err);
      } finally {
        setBusy(false);
      }
    }

    async function resetCatalog() {
      if (!confirm("Xóa toàn bộ catalog sản phẩm đã nạp?")) return;
      setBusy(true);
      try {
        log(await api("/api/reset-catalog", {}));
        await refresh();
      } catch (err) {
        log(err);
      } finally {
        setBusy(false);
      }
    }

    async function resetAlbumCache() {
      if (!confirm("Xóa cache album Google Photos? App sẽ tạo album mới khi upload tiếp theo nếu cần.")) return;
      setBusy(true);
      try {
        log(await api("/api/reset-album-cache", {}));
        await refresh();
      } catch (err) {
        log(err);
      } finally {
        setBusy(false);
      }
    }

    const browserKey = localStorage.getItem("pixel_agent_openai_api_key");
    if (browserKey) {
      document.getElementById("openaiApiKey").value = browserKey;
    }
    const browserGeminiKey = localStorage.getItem("pixel_agent_gemini_api_key");
    if (browserGeminiKey) {
      document.getElementById("geminiApiKey").value = browserGeminiKey;
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


def env_path() -> Path:
    return ROOT / ".env"


def load_env_values() -> dict[str, str]:
    values: dict[str, str] = {}
    path = env_path()
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def save_env_values(values: dict[str, str]) -> None:
    ordered_keys = [
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "SERPAPI_API_KEY",
        "GOOGLE_CSE_API_KEY",
        "GOOGLE_CSE_CX",
        "BING_SEARCH_API_KEY",
    ]
    lines: list[str] = []
    for key in ordered_keys:
        if values.get(key):
            lines.append(f"{key}={values[key]}")
    for key in sorted(k for k in values if k not in ordered_keys and values[k]):
        lines.append(f"{key}={values[key]}")
    env_path().write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    for key, value in values.items():
        if value:
            os.environ[key] = value


def update_classification_config(updates: dict[str, Any]) -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config.setdefault("classification", {}).update(updates)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def active_search_key(values: dict[str, str], provider: str) -> str:
    provider = provider.lower().strip()
    if provider == "serpapi":
        return os.environ.get("SERPAPI_API_KEY") or values.get("SERPAPI_API_KEY", "")
    if provider == "google_cse":
        return os.environ.get("GOOGLE_CSE_API_KEY") or values.get("GOOGLE_CSE_API_KEY", "")
    if provider == "bing":
        return os.environ.get("BING_SEARCH_API_KEY") or values.get("BING_SEARCH_API_KEY", "")
    return ""


def normalize_google_cse_cx(value: str) -> str:
    value = (value or "").strip()
    if "cx=" not in value:
        return value.strip().strip('"').strip("'")
    tail = value.split("cx=", 1)[1]
    for separator in ['"', "'", "&", ">", " ", "\n", "\r"]:
        if separator in tail:
            tail = tail.split(separator, 1)[0]
    return tail.strip().strip('"').strip("'")


def parse_float_input(value: Any, default: float) -> float:
    if value is None or value == "":
        return default
    return float(str(value).replace(",", "."))


def masked_key(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 12:
        return "*" * len(value)
    return f"{value[:7]}...{value[-4:]}"


def check_openai_key(api_key: str) -> dict[str, Any]:
    import requests

    if not api_key:
        raise ValueError("Chua co OpenAI API key de kiem tra.")
    response = requests.get(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    if response.status_code == 200:
        return {"ok": True, "status": "connected", "message": "GPT API dang hoat dong."}
    if response.status_code in {401, 403}:
        return {"ok": False, "status": "auth_error", "message": "Key khong hop le hoac khong co quyen truy cap."}
    if response.status_code == 429:
        return {"ok": False, "status": "rate_or_quota", "message": "Key bi gioi han toc do hoac het quota."}
    return {"ok": False, "status": f"http_{response.status_code}", "message": response.text[:500]}


def check_gemini_key(api_key: str) -> dict[str, Any]:
    import requests

    if not api_key:
        raise ValueError("Chua co Gemini API key de kiem tra.")
    response = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        params={"key": api_key},
        timeout=30,
    )
    if response.status_code == 200:
        return {"ok": True, "status": "connected", "message": "Gemini API dang hoat dong."}
    if response.status_code in {400, 401, 403}:
        return {"ok": False, "status": "auth_error", "message": "Key khong hop le hoac khong co quyen truy cap."}
    if response.status_code == 429:
        return {"ok": False, "status": "rate_or_quota", "message": "Key bi gioi han toc do hoac het quota."}
    return {"ok": False, "status": f"http_{response.status_code}", "message": response.text[:500]}


def check_search_key(provider: str, values: dict[str, str]) -> dict[str, Any]:
    import requests

    provider = provider.lower().strip()
    if provider == "serpapi":
        api_key = values.get("SERPAPI_API_KEY") or os.environ.get("SERPAPI_API_KEY", "")
        if not api_key:
            raise ValueError("Chua co SERPAPI_API_KEY.")
        response = requests.get(
            "https://serpapi.com/search.json",
            params={"engine": "google_images", "q": "test product", "api_key": api_key},
            timeout=30,
        )
    elif provider == "google_cse":
        api_key = values.get("GOOGLE_CSE_API_KEY") or os.environ.get("GOOGLE_CSE_API_KEY", "")
        cx = values.get("GOOGLE_CSE_CX") or os.environ.get("GOOGLE_CSE_CX", "")
        if not api_key or not cx:
            raise ValueError("Chua co GOOGLE_CSE_API_KEY hoac GOOGLE_CSE_CX.")
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"key": api_key, "cx": cx, "q": "test product", "searchType": "image", "num": 1},
            timeout=30,
        )
    elif provider == "bing":
        api_key = values.get("BING_SEARCH_API_KEY") or os.environ.get("BING_SEARCH_API_KEY", "")
        if not api_key:
            raise ValueError("Chua co BING_SEARCH_API_KEY.")
        response = requests.get(
            "https://api.bing.microsoft.com/v7.0/images/search",
            headers={"Ocp-Apim-Subscription-Key": api_key},
            params={"q": "test product", "count": 1},
            timeout=30,
        )
    else:
        raise ValueError(f"Search provider khong hop le: {provider}")
    if response.status_code == 200:
        return {"ok": True, "status": "connected", "message": f"{provider} search API dang hoat dong."}
    if response.status_code in {400, 401, 403}:
        return {"ok": False, "status": "auth_error", "message": "Search API key/cau hinh khong hop le."}
    if response.status_code == 429:
        return {"ok": False, "status": "rate_or_quota", "message": "Search API bi gioi han toc do hoac het quota."}
    return {"ok": False, "status": f"http_{response.status_code}", "message": response.text[:500]}


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
    if provider in {"both", "openai+gemini", "dual"}:
        cfg.classification_mode = "ai"
        cfg.ai_provider = "both"
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
    values = load_env_values()
    search_key = active_search_key(values, cfg.web_enrichment_provider)
    return jsonify(
        {
            "adb_device": devices[0] if devices else "",
            "google_token": cfg.token_file.exists(),
            "openai_key": bool(os.environ.get("OPENAI_API_KEY") or values.get("OPENAI_API_KEY")),
            "openai_key_masked": masked_key(os.environ.get("OPENAI_API_KEY") or values.get("OPENAI_API_KEY")),
            "gemini_key": bool(os.environ.get("GEMINI_API_KEY") or values.get("GEMINI_API_KEY")),
            "gemini_key_masked": masked_key(os.environ.get("GEMINI_API_KEY") or values.get("GEMINI_API_KEY")),
            "search_key": bool(search_key),
            "search_key_masked": masked_key(search_key),
            "search_provider": cfg.web_enrichment_provider,
            "web_enrichment_enabled": cfg.web_enrichment_enabled,
            "web_confidence_threshold": cfg.web_enrichment_confidence_threshold,
            "ai_provider": cfg.ai_provider if cfg.classification_mode == "ai" else "offline",
            "products": pipeline.product_names(cfg),
        }
    )


@app.post("/api/settings/api-key")
def api_save_api_key():
    try:
        payload = request.json or {}
        provider = (payload.get("provider") or "openai").lower().strip()
        api_key = (payload.get("api_key") or "").strip()
        if provider == "openai" and not api_key.startswith(("sk-", "sk-proj-")):
            raise ValueError("OpenAI API key khong dung dinh dang mong doi.")
        if provider == "gemini" and not api_key.startswith("AIza"):
            raise ValueError("Gemini API key khong dung dinh dang mong doi.")
        if provider not in {"openai", "gemini"}:
            raise ValueError("Provider khong hop le.")

        values = load_env_values()
        env_name = "OPENAI_API_KEY" if provider == "openai" else "GEMINI_API_KEY"
        values[env_name] = api_key
        save_env_values(values)
        return jsonify({"status": "saved", "provider": provider, "key_masked": masked_key(api_key)})
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/settings/check-openai")
def api_check_openai():
    try:
        payload = request.json or {}
        api_key = (payload.get("api_key") or "").strip()
        if not api_key:
            values = load_env_values()
            api_key = os.environ.get("OPENAI_API_KEY") or values.get("OPENAI_API_KEY", "")
        result = check_openai_key(api_key)
        result["openai_key_masked"] = masked_key(api_key)
        return jsonify(result)
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/settings/check-gemini")
def api_check_gemini():
    try:
        payload = request.json or {}
        api_key = (payload.get("api_key") or "").strip()
        if not api_key:
            values = load_env_values()
            api_key = os.environ.get("GEMINI_API_KEY") or values.get("GEMINI_API_KEY", "")
        result = check_gemini_key(api_key)
        result["gemini_key_masked"] = masked_key(api_key)
        return jsonify(result)
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/settings/search")
def api_save_search_settings():
    try:
        payload = request.json or {}
        provider = (payload.get("provider") or "serpapi").lower().strip()
        api_key = (payload.get("api_key") or "").strip()
        cx = normalize_google_cse_cx(payload.get("google_cse_cx") or "")
        threshold = parse_float_input(payload.get("confidence_threshold"), 0.78)
        if provider not in {"serpapi", "google_cse", "bing"}:
            raise ValueError("Search provider khong hop le.")
        values = load_env_values()
        if api_key:
            if provider == "serpapi":
                values["SERPAPI_API_KEY"] = api_key
            elif provider == "google_cse":
                values["GOOGLE_CSE_API_KEY"] = api_key
            elif provider == "bing":
                values["BING_SEARCH_API_KEY"] = api_key
        if cx:
            values["GOOGLE_CSE_CX"] = cx
        save_env_values(values)
        update_classification_config(
            {
                "web_enrichment_enabled": True,
                "web_enrichment_provider": provider,
                "web_enrichment_confidence_threshold": max(0.0, min(threshold, 1.0)),
            }
        )
        return jsonify(
            {
                "status": "saved",
                "provider": provider,
                "has_key": bool(active_search_key(values, provider)),
                "confidence_threshold": max(0.0, min(threshold, 1.0)),
            }
        )
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/settings/check-search")
def api_check_search():
    try:
        payload = request.json or {}
        provider = (payload.get("provider") or "serpapi").lower().strip()
        values = load_env_values()
        return jsonify(check_search_key(provider, values))
    except Exception as exc:
        return error_response(exc, 400)


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


@app.post("/api/reset-album-cache")
def api_reset_album_cache():
    try:
        cfg = settings()
        pipeline.save_album_cache(cfg, {})
        return jsonify({"status": "reset", "album_cache": str(cfg.album_cache_file)})
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


@app.post("/api/record-upload")
def api_record_upload():
    try:
        cfg = settings()
        set_provider(cfg, request.json.get("provider", cfg.ai_provider))
        forced_product = (request.json.get("product") or "").strip() or None
        duration = int(request.json.get("duration") or 10)

        reference_image = None
        if forced_product:
            product, score, reason = forced_product, None, "forced by user"
        else:
            reference_image = pipeline.capture_from_pixel(cfg)
            product, score, reason = pipeline.classify_product(cfg, reference_image)

        video = pipeline.capture_video_from_pixel(cfg, duration)
        result = pipeline.upload_media(cfg, video, product, "Product video")
        return jsonify(
            {
                "captured": str(video),
                "reference_image": str(reference_image) if reference_image else None,
                "product": product,
                "score": score,
                "reason": reason,
                "duration": max(1, min(duration, 300)),
                **pipeline.upload_result_summary(result),
            }
        )
    except Exception as exc:
        return error_response(exc)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8765")), debug=False)
