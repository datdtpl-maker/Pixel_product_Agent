from __future__ import annotations

import json
import os
import re
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
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      color-scheme: dark;
      --bg: #07090e;
      --panel: rgba(17, 22, 37, 0.65);
      --panel-border: rgba(255, 255, 255, 0.08);
      --soft: rgba(255, 255, 255, 0.03);
      --line: rgba(255, 255, 255, 0.06);
      --text: #f3f4f6;
      --muted: #9ca3af;
      --brand: #3b82f6;
      --brand-hover: #2563eb;
      --brand-gradient: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
      --brand-glow: rgba(59, 130, 246, 0.3);
      --ok: #10b981;
      --okbg: rgba(16, 185, 129, 0.1);
      --warn: #f59e0b;
      --warnbg: rgba(245, 158, 11, 0.1);
      --danger: #ef4444;
      --danger-hover: #dc2626;
      --danger-gradient: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
      --shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    body.theme-light {
      color-scheme: light;
      --bg: #f4f7fa;
      --panel: rgba(255, 255, 255, 0.85);
      --panel-border: rgba(0, 0, 0, 0.07);
      --soft: rgba(0, 0, 0, 0.02);
      --line: rgba(0, 0, 0, 0.05);
      --text: #1e293b;
      --muted: #64748b;
      --brand: #2563eb;
      --brand-hover: #1d4ed8;
      --brand-glow: rgba(37, 99, 235, 0.15);
      --ok: #059669;
      --okbg: rgba(5, 150, 105, 0.08);
      --warn: #d97706;
      --warnbg: rgba(217, 119, 6, 0.08);
      --danger: #dc2626;
      --danger-hover: #b91c1c;
      --shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
    }
    
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: radial-gradient(circle at top left, rgba(59, 130, 246, 0.07), transparent 45%),
                  radial-gradient(circle at bottom right, rgba(139, 92, 246, 0.07), transparent 45%),
                  var(--bg);
      color: var(--text);
      min-height: 100vh;
      transition: background 0.3s, color 0.3s;
    }
    button, input, select { font: inherit; }
    button {
      min-height: 42px;
      border: 0;
      border-radius: 10px;
      padding: 10px 16px;
      background: var(--brand-gradient);
      color: #fff;
      font-weight: 700;
      font-family: 'Plus Jakarta Sans', sans-serif;
      cursor: pointer;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 4px 12px var(--brand-glow);
    }
    button:hover {
      background: var(--brand-hover);
      transform: translateY(-2px);
      box-shadow: 0 6px 18px var(--brand-glow);
    }
    button:active {
      transform: translateY(0);
    }
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none !important;
      box-shadow: none !important;
    }
    button.secondary {
      background: rgba(255, 255, 255, 0.06);
      color: var(--text);
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: none;
      transition: background 0.3s, color 0.3s, border-color 0.3s;
    }
    body.theme-light button.secondary {
      background: rgba(0, 0, 0, 0.03);
      color: var(--text);
      border: 1px solid rgba(0, 0, 0, 0.08);
    }
    button.secondary:hover {
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(255, 255, 255, 0.15);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    body.theme-light button.secondary:hover {
      background: rgba(0, 0, 0, 0.06);
      border-color: rgba(0, 0, 0, 0.12);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    button.ghost {
      background: transparent;
      color: var(--muted);
      border: 1px solid rgba(255, 255, 255, 0.05);
      box-shadow: none;
    }
    body.theme-light button.ghost {
      border-color: rgba(0, 0, 0, 0.05);
    }
    button.ghost:hover {
      background: rgba(255, 255, 255, 0.05);
      color: var(--text);
      border-color: rgba(255, 255, 255, 0.1);
    }
    body.theme-light button.ghost:hover {
      background: rgba(0, 0, 0, 0.03);
      color: var(--text);
      border-color: rgba(0, 0, 0, 0.1);
    }
    button.danger {
      background: var(--danger-gradient);
      box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
    }
    button.danger:hover {
      background: var(--danger-hover);
      box-shadow: 0 6px 18px rgba(239, 68, 68, 0.3);
    }
    button.btn-capture {
      background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
      box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3);
    }
    button.btn-capture:hover {
      background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
      box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
    }
    button.btn-record {
      background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%);
      box-shadow: 0 4px 14px rgba(225, 29, 72, 0.3);
    }
    button.btn-record:hover {
      background: linear-gradient(135deg, #fb7185 0%, #f43f5e 100%);
      box-shadow: 0 6px 20px rgba(225, 29, 72, 0.4);
    }
    input, select {
      width: 100%;
      min-height: 44px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 10px;
      background: rgba(13, 17, 28, 0.6);
      padding: 10px 14px;
      color: var(--text);
      outline: none;
      transition: all 0.2s;
    }
    body.theme-light input, body.theme-light select {
      background: #fff;
      border-color: #cbd5e1;
      color: var(--text);
    }
    input:focus, select:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 3px var(--brand-glow);
    }
    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 600;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--muted);
      font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .shell {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .sidebar { display: none; }
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
    }
    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 20px;
      padding: 20px 32px;
      background: rgba(10, 14, 23, 0.7);
      border-bottom: 1px solid var(--panel-border);
      position: sticky;
      top: 0;
      z-index: 10;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      transition: background 0.3s, border-color 0.3s;
    }
    body.theme-light .topbar {
      background: rgba(240, 244, 248, 0.85);
    }
    .topbar h2 {
      margin: 0;
      font-size: 22px;
      font-weight: 800;
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: linear-gradient(135deg, #fff 40%, #a5b4fc 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      transition: all 0.3s;
    }
    body.theme-light .topbar h2 {
      background: linear-gradient(135deg, #0f172a 40%, #1e3a8a 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .topbar p {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 14px;
    }
    .actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .content {
      padding: 32px;
      flex: 1;
      max-width: 1600px;
      width: 100%;
      margin: 0 auto;
    }
    .workspace {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 440px;
      gap: 24px;
      align-items: start;
    }
    .work-main {
      display: grid;
      gap: 24px;
      min-width: 0;
    }
    .work-log {
      position: sticky;
      top: 112px;
      min-width: 0;
    }
    .metrics {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 16px;
    }
    .metric {
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 14px;
      box-shadow: var(--shadow);
      padding: 18px;
      min-height: 96px;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .metric:hover {
      transform: translateY(-2px);
      border-color: rgba(59, 130, 246, 0.25);
      box-shadow: 0 12px 30px rgba(59, 130, 246, 0.08);
    }
    body.theme-light .metric strong {
      color: #0f172a;
    }
    .metric small {
      display: block;
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 8px;
    }
    .metric strong {
      display: block;
      font-size: 15px;
      font-weight: 700;
      color: #fff;
      overflow-wrap: anywhere;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      font-weight: 700;
      gap: 6px;
      line-height: 1.2;
    }
    .badge.ok {
      background: var(--okbg);
      color: var(--ok);
      border: 1px solid rgba(16, 185, 129, 0.15);
    }
    .badge.ok::before {
      content: '';
      display: inline-block;
      width: 6px;
      height: 6px;
      background: var(--ok);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--ok);
      animation: pulse 1.8s infinite;
    }
    .badge.warn {
      background: var(--warnbg);
      color: var(--warn);
      border: 1px solid rgba(245, 158, 11, 0.15);
    }
    .badge.warn::before {
      content: '';
      display: inline-block;
      width: 6px;
      height: 6px;
      background: var(--warn);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--warn);
      animation: pulse 1.8s infinite;
    }
    @keyframes pulse {
      0% { transform: scale(0.95); opacity: 0.6; }
      50% { transform: scale(1.15); opacity: 1; box-shadow: 0 0 10px currentColor; }
      100% { transform: scale(0.95); opacity: 0.6; }
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 16px;
      box-shadow: var(--shadow);
      overflow: hidden;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      transition: background 0.3s, border-color 0.3s, box-shadow 0.3s;
    }
    .panel-head {
      padding: 20px 24px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.01);
      transition: border-color 0.3s;
    }
    .panel-head h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      font-family: 'Plus Jakarta Sans', sans-serif;
      color: #fff;
      transition: color 0.3s;
    }
    body.theme-light .panel-head h3 {
      color: #0f172a;
    }
    .panel-head p {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .panel-body {
      padding: 24px;
      display: grid;
      gap: 20px;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr);
      gap: 24px;
      align-items: start;
    }
    .two {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    .field-action {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: end;
    }
    .hint {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      display: flex;
      align-items: flex-start;
      gap: 6px;
    }
    .hint::before {
      content: 'ℹ';
      color: var(--brand);
      font-weight: bold;
    }
    .steps {
      display: grid;
      gap: 12px;
    }
    .step {
      display: grid;
      grid-template-columns: 32px 1fr;
      gap: 12px;
      padding: 14px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.04);
      border-radius: 12px;
      transition: all 0.25s;
    }
    body.theme-light .step {
      background: rgba(0, 0, 0, 0.01);
      border-color: rgba(0, 0, 0, 0.04);
    }
    .step:hover {
      background: rgba(255, 255, 255, 0.04);
      border-color: rgba(255, 255, 255, 0.08);
      transform: translateX(4px);
    }
    body.theme-light .step:hover {
      background: rgba(0, 0, 0, 0.03);
      border-color: rgba(0, 0, 0, 0.08);
    }
    .step span {
      display: grid;
      place-items: center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      font-weight: 800;
      font-family: 'Plus Jakarta Sans', sans-serif;
      transition: all 0.3s;
    }
    body.theme-light .step span {
      background: rgba(37, 99, 235, 0.08);
      color: #2563eb;
    }
    .step b {
      display: block;
      margin-bottom: 4px;
      font-size: 14px;
      color: #fff;
      transition: color 0.3s;
    }
    body.theme-light .step b {
      color: #0f172a;
    }
    .step small {
      display: block;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }
    .control-grid {
      display: grid;
      grid-template-columns: minmax(220px, 320px) minmax(0, 1fr);
      gap: 20px;
      align-items: end;
    }
    .control-note {
      padding: 16px;
      border: 1px solid rgba(255, 255, 255, 0.04);
      background: rgba(255, 255, 255, 0.02);
      border-radius: 12px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
      transition: background 0.3s, border-color 0.3s;
    }
    body.theme-light .control-note {
      background: rgba(0, 0, 0, 0.015);
      border-color: rgba(0, 0, 0, 0.05);
    }
    .logbox {
      background: #090c13;
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      overflow: hidden;
      box-shadow: inset 0 4px 12px rgba(0, 0, 0, 0.5);
      transition: background 0.3s, border-color 0.3s, box-shadow 0.3s;
    }
    body.theme-light .logbox {
      background: #f8fafc;
      border-color: #e2e8f0;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
    }
    .loghead {
      display: flex;
      justify-content: space-between;
      padding: 12px 16px;
      color: var(--text);
      background: rgba(255, 255, 255, 0.02);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      font-size: 13px;
      font-weight: 700;
      font-family: 'Plus Jakarta Sans', sans-serif;
      transition: background 0.3s, border-color 0.3s, color 0.3s;
    }
    body.theme-light .loghead {
      background: #f1f5f9;
      border-bottom-color: #e2e8f0;
      color: #334155;
    }
    .log {
      min-height: 520px;
      max-height: calc(100vh - 250px);
      overflow: auto;
      padding: 16px;
      font: 13px/1.5 Consolas, "Cascadia Mono", monospace;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .log-item {
      border-left: 3px solid var(--brand);
      padding: 8px 12px;
      border-radius: 0 6px 6px 0;
      background: rgba(255, 255, 255, 0.015);
      animation: fadeIn 0.3s ease-out;
      transition: background 0.3s, border-color 0.3s;
    }
    body.theme-light .log-item {
      background: #fff;
      border: 1px solid #e2e8f0;
      border-left-width: 3px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }
    .log-item.log-error {
      border-left-color: var(--danger);
      background: rgba(239, 68, 68, 0.05);
    }
    body.theme-light .log-item.log-error {
      border-left-color: var(--danger);
      background: rgba(239, 68, 68, 0.02);
    }
    .log-item.log-success {
      border-left-color: var(--ok);
      background: rgba(16, 185, 129, 0.05);
    }
    body.theme-light .log-item.log-success {
      border-left-color: var(--ok);
      background: rgba(16, 185, 129, 0.02);
    }
    .log-item.log-warning {
      border-left-color: var(--warn);
      background: rgba(245, 158, 11, 0.05);
    }
    body.theme-light .log-item.log-warning {
      border-left-color: var(--warn);
      background: rgba(245, 158, 11, 0.02);
    }
    .log-time {
      color: #6b7280;
      font-size: 11px;
      font-weight: 600;
      display: block;
      margin-bottom: 4px;
    }
    .log-text {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-all;
      color: #e5e7eb;
      transition: color 0.3s;
    }
    body.theme-light .log-text {
      color: #1e293b;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .buttons {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    @media(max-width: 1280px) {
      .workspace { grid-template-columns: 1fr; }
      .work-log { position: static; }
      .log { min-height: 280px; max-height: 420px; }
    }
    @media(max-width: 960px) {
      .metrics { grid-template-columns: repeat(3, 1fr); }
      .layout, .control-grid { grid-template-columns: 1fr; }
      .topbar { flex-direction: column; align-items: stretch; padding: 18px 24px; }
      .actions { margin-top: 12px; }
    }
    @media(max-width: 640px) {
      .metrics { grid-template-columns: 1fr; }
      .two, .field-action { grid-template-columns: 1fr; }
      .content { padding: 16px; }
      .buttons button, .actions button { width: 100%; }
    }
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
      <div>
        <h2>Trung tâm chụp sản phẩm</h2>
        <p>Chọn thư mục trước, sau đó chụp hoặc quay từ Pixel.</p>
      </div>
      <div class="actions">
        <button id="themeToggleBtn" class="secondary" onclick="toggleTheme()">
          <!-- Chèn icon SVG tự động bằng Javascript -->
        </button>
        <button class="ghost" onclick="refresh()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
          Làm mới
        </button>
        <button class="secondary" onclick="openPreview()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
          Xem Pixel
        </button>
        <button class="secondary" onclick="togglePixelScreen()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"></path><line x1="12" y1="2" x2="12" y2="12"></line></svg>
          Bật / tắt Pixel
        </button>
        <button class="btn-capture" onclick="capture()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
          Chụp ảnh
        </button>
        <button class="btn-record" onclick="record()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"></polygon><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
          Quay video
        </button>
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
              <button onclick="saveDriveRoot()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
                Lưu & quét lại
              </button>
            </div>
            <div class="two">
              <div><label for="folderSelect">Chọn thư mục sản phẩm</label><select id="folderSelect" onchange="selectFolder()"><option value="">-- Chưa chọn thư mục --</option></select></div>
              <div><label for="newFolder">Tạo thư mục sản phẩm mới</label><div class="field-action"><input id="newFolder" placeholder="Ví dụ: Eskar Tears 15ml"><button onclick="createFolder()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>Tạo</button></div></div>
            </div>
            <div class="buttons">
              <button class="secondary" onclick="scanFolders()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                Quét lại thư mục
              </button>
              <button class="danger" onclick="deleteFolder()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                Xóa thư mục đang chọn
              </button>
            </div>
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
        <div class="panel-head"><h3>Cấu hình hệ thống & kết nối</h3><p>Thiết lập thời lượng quay video và phương thức kết nối điều khiển Pixel.</p></div>
        <div class="panel-body">
          <div class="two">
            <div>
              <label for="duration">Thời lượng video (giây)</label>
              <input id="duration" type="number" min="1" max="300" value="10">
              <div class="hint" style="margin-top: 6px;">Giới hạn từ 1 đến 300 giây cho mỗi lần quay.</div>
            </div>
            <div>
              <label for="connMode">Kiểu kết nối Pixel</label>
              <select id="connMode" onchange="changeConnMode()">
                <option value="usb">🔌 Cắm cáp USB vật lý</option>
                <option value="wifi">📶 Kết nối Wi-Fi không dây</option>
              </select>
              
              <div id="wifiIpGroup" style="margin-top: 12px; display: none;">
                <label for="wifiIp">Địa chỉ IP của Pixel (Wi-Fi)</label>
                <div class="field-action">
                  <input id="wifiIp" placeholder="Ví dụ: 192.168.1.18">
                  <button class="secondary" onclick="detectPixelIp()" title="Dò tìm IP tự động khi đang cắm cáp USB">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    Quét IP (USB)
                  </button>
                  <button onclick="saveConnSettings()">Kết nối Wifi</button>
                </div>
                <div class="hint" style="margin-top: 6px;">Cắm cáp USB rồi bấm "Quét IP (USB)" để tự động dò IP, sau đó bấm "Kết nối Wifi" và rút cáp ra.</div>
              </div>
            </div>
          </div>
        </div>
      </section>
      </div>

      <aside class="panel work-log">
        <div class="panel-head"><h3>Nhật ký xử lý</h3><p>Theo dõi từng bước: chụp/quay, kéo file, chép vào Drive và xóa khỏi Pixel.</p></div>
        <div class="panel-body">
          <div class="buttons"><button class="ghost" onclick="clearLog()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>Xóa log</button></div>
          <div class="logbox">
            <div class="loghead"><span>Event stream</span><span id="logCount">0 events</span></div>
            <div id="log" class="log"></div>
          </div>
        </div>
      </aside>
      </div>
    </div>
  </main>
</div>
<script>
  const logBox=document.getElementById("log"); let eventCount=0,lastId=0,poller=null,busy=false;
  
  function initTheme() {
    const theme = localStorage.getItem('theme') || 'dark';
    if (theme === 'light') {
      document.body.classList.add('theme-light');
    }
    updateThemeButton();
  }
  
  function toggleTheme() {
    const isLight = document.body.classList.toggle('theme-light');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    updateThemeButton();
  }
  
  function updateThemeButton() {
    const isLight = document.body.classList.contains('theme-light');
    const btn = document.getElementById('themeToggleBtn');
    if (isLight) {
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg> Giao diện tối`;
    } else {
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg> Giao diện sáng`;
    }
  }

  function changeConnMode() {
    const mode = document.getElementById("connMode").value;
    const ipGroup = document.getElementById("wifiIpGroup");
    if (mode === "wifi") {
      ipGroup.style.display = "block";
    } else {
      ipGroup.style.display = "none";
    }
  }

  async function detectPixelIp() {
    try {
      log({status: "Đang quét thiết bị Pixel cắm cáp USB để tự động lấy địa chỉ IP..."});
      const d = await api("/api/pixel/detect-ip", {});
      log(d);
      if (d.ip) {
        document.getElementById("wifiIp").value = d.ip;
        log({status: `Đã tự động dò tìm IP wlan0: ${d.ip}. Tiến hành lưu cấu hình...`});
        await saveConnSettings();
      }
    } catch(e) {
      log(e);
    }
  }

  async function saveConnSettings() {
    try {
      const mode = document.getElementById("connMode").value;
      const ip = document.getElementById("wifiIp").value.trim();
      
      if (mode === "wifi" && !ip) {
        log({error: "Vui lòng nhập địa chỉ IP của Pixel để kết nối Wi-Fi."});
        return;
      }
      
      log({status: `Đang lưu cấu hình kết nối qua ${mode.toUpperCase()}...`});
      const d = await api("/api/pixel/connection", {
        connection_mode: mode,
        wifi_ip: ip
      });
      log(d);
      await refresh();
    } catch(e) {
      log(e);
    }
  }

  function log(v) {
    eventCount++;
    document.getElementById("logCount").textContent = `${eventCount} events`;
    
    let isError = false;
    let isSuccess = false;
    let isWarning = false;
    let text = "";
    
    if (typeof v === "string") {
      text = v;
      if (v.toLowerCase().includes("lỗi") || v.toLowerCase().includes("error") || v.toLowerCase().includes("failed")) isError = true;
    } else {
      text = JSON.stringify(v, null, 2);
      const step = v.step || "";
      if (step === "error" || v.error) isError = true;
      if (step === "done" || step === "drive_saved" || step === "pulled" || step === "capture" || step === "record" || step === "wifi_connected" || step === "usb_mode" || step === "ip_detected") isSuccess = true;
      if (step === "cleanup" && v.cleanup_warning) isWarning = true;
    }
    
    let colorClass = "log-info";
    if (isError) colorClass = "log-error";
    else if (isSuccess) colorClass = "log-success";
    else if (isWarning) colorClass = "log-warning";
    
    const timeStr = new Date().toLocaleTimeString();
    const escText = escapeHtml(text);
    const logItem = `<div class="log-item ${colorClass}">
      <span class="log-time">[${timeStr}]</span>
      <pre class="log-text">${escText}</pre>
    </div>`;
    
    logBox.innerHTML = logItem + logBox.innerHTML;
  }
  function clearLog(){eventCount=0;lastId=0;logBox.innerHTML="";document.getElementById("logCount").textContent="0 events"}
  async function api(path,body){const r=await fetch(path,{method:body?"POST":"GET",headers:body?{"Content-Type":"application/json"}:{},body:body?JSON.stringify(body):undefined});const d=await r.json();if(!r.ok)throw d;return d}
  async function pull(){const d=await api(`/api/events?after=${lastId}`);for(const e of d.events||[]){lastId=Math.max(lastId,e.id||0);log(e.payload)}}
  function startPoll(){if(!poller){pull().catch(()=>{});poller=setInterval(()=>pull().catch(()=>{}),700)}}
  async function stopPoll(){if(poller){clearInterval(poller);poller=null}await pull().catch(()=>{})}
  function selected(){return document.getElementById("folderSelect").value}
  function requireFolder(){if(!selected()){log({error:"Hãy chọn hoặc tạo thư mục sản phẩm trước khi chụp/quay."});return false}return true}
  function setBusy(v){busy=v;document.querySelectorAll("button").forEach(b=>b.disabled=v);document.getElementById("themeToggleBtn").disabled=false;if(document.querySelector("#wifiIpGroup button")) document.querySelectorAll("#wifiIpGroup button").forEach(b=>b.disabled=v);}
  function render(d){document.getElementById("adbMetric").innerHTML=d.adb_device?`<span class="badge ok">${d.adb_device}</span>`:`<span class="badge warn">Chưa thấy Pixel</span>`;document.getElementById("driveMetric").innerHTML=d.drive_ready?`<span class="badge ok">Đã kết nối</span>`:`<span class="badge warn">Không tìm thấy</span>`;document.getElementById("selectedMetric").textContent=d.selected_folder||"Chưa chọn";document.getElementById("folderMetric").textContent=(d.folders||[]).length;document.getElementById("busyMetric").innerHTML=d.operation_busy?'<span class="badge warn">Đang xử lý</span>':'<span class="badge ok">Sẵn sàng</span>';document.getElementById("navFolders").textContent=(d.folders||[]).length;document.getElementById("navDrive").textContent=d.drive_ready?"OK":"Lỗi";document.getElementById("navAdb").textContent=d.adb_device?"OK":"Offline";document.getElementById("driveRoot").value=d.drive_root;document.getElementById("connMode").value=d.connection_mode||"usb";document.getElementById("wifiIp").value=d.wifi_ip||"";changeConnMode();const s=document.getElementById("folderSelect"),current=d.selected_folder||s.value;s.innerHTML='<option value="">-- Chưa chọn thư mục --</option>'+d.folders.map(f=>`<option value="${escapeHtml(f)}">${escapeHtml(f)}</option>`).join("");s.value=current}
  function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
  async function refresh(){try{render(await api("/api/status"))}catch(e){log(e)}}
  async function scanFolders(){try{render(await api("/api/status"));log({status:"Đã quét lại danh sách thư mục."})}catch(e){log(e)}}
  async function saveDriveRoot(){try{log(await api("/api/drive-root",{drive_root:document.getElementById("driveRoot").value}));await refresh()}catch(e){log(e)}}
  async function createFolder(){try{const d=await api("/api/folders",{name:document.getElementById("newFolder").value});document.getElementById("newFolder").value="";log(d);await refresh()}catch(e){log(e)}}
  async function deleteFolder(){const name=selected();if(!name){log({error:"Hãy chọn thư mục cần xóa."});return}if(!confirm(`Xóa thư mục rỗng "${name}"?`))return;try{log(await api("/api/folders/delete",{name}));await refresh()}catch(e){log(e)}}
  async function selectFolder(){try{const d=await api("/api/select-folder",{name:selected()});log(d);await refresh()}catch(e){log(e)}}
  async function openPreview(){try{log(await api("/api/open-preview",{}))}catch(e){log(e)}}
  async function togglePixelScreen(){try{log(await api("/api/toggle-screen",{}));await refresh()}catch(e){log(e)}}
  async function run(path,body){if(!requireFolder()||busy)return;setBusy(true);await api("/api/events/clear",{}).catch(()=>{});lastId=0;startPoll();try{log(await api(path,body));await refresh()}catch(e){log(e)}finally{await stopPoll();setBusy(false)}}
  function capture(){run("/api/capture",{folder:selected()})}
  function record(){run("/api/record",{folder:selected(),duration:Number(document.getElementById("duration").value||10)})}
  initTheme();
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
    config = load_config()
    pixel_cfg = config.get("pixel", {})
    connection_mode = pixel_cfg.get("connection_mode", "usb")
    wifi_ip = pixel_cfg.get("wifi_ip", "").strip()

    # Quét danh sách thiết bị hiện có
    output = pipeline.adb_command(cfg, "devices", check=False).stdout.splitlines()
    devices = []
    for line in output:
        if "\tdevice" in line:
            devices.append(line.split()[0])

    if connection_mode == "wifi":
        if not wifi_ip:
            raise ValueError("Chưa cấu hình địa chỉ IP của Pixel để kết nối không dây.")
        target_serial = f"{wifi_ip}:5555"
        
        # Nếu chưa kết nối wifi, thử adb connect
        if target_serial not in devices:
            pipeline.adb_command(cfg, "connect", target_serial, check=False)
            # Quét lại danh sách thiết bị
            output = pipeline.adb_command(cfg, "devices", check=False).stdout.splitlines()
            devices = [line.split()[0] for line in output if "\tdevice" in line]
            
        if target_serial not in devices:
            raise RuntimeError(f"Không thể kết nối đến Pixel qua Wifi tại {target_serial}. Hãy kiểm tra IP điện thoại và đảm bảo bắt chung Wifi.")
        return target_serial
    else:
        # Chế độ USB: Lọc các thiết bị không chứa dấu hai chấm ':' (tức là không phải IP mạng)
        usb_devices = [d for d in devices if ":" not in d]
        if not usb_devices:
            # Nếu không tìm thấy qua USB nhưng có cấu hình adb_serial trong config.json
            if cfg.adb_serial and cfg.adb_serial in devices:
                return cfg.adb_serial
            raise RuntimeError("Chưa thấy Pixel cắm cáp USB. Hãy kiểm tra cáp và USB debugging.")
        if len(usb_devices) > 1:
            if cfg.adb_serial and cfg.adb_serial in usb_devices:
                return cfg.adb_serial
            raise RuntimeError("Có nhiều thiết bị USB. Điền adb_serial trong config.json để chọn thiết bị.")
        return usb_devices[0]


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


def sleep_pixel(cfg: pipeline.Settings) -> None:
    pipeline.adb_command(cfg, "shell", "input", "keyevent", "223", check=False)


def wake_pixel(cfg: pipeline.Settings) -> None:
    pipeline.adb_command(cfg, "shell", "input", "keyevent", "224", check=False)


def pixel_screen_is_on(cfg: pipeline.Settings) -> bool:
    result = pipeline.adb_command(cfg, "shell", "dumpsys", "power", check=False)
    output = f"{result.stdout}\n{result.stderr}"
    lowered = output.lower()
    compact = lowered.replace(" ", "")
    if "display power: state=on" in lowered or "mholdingdisplaywakelockssuspendblocker=true" in lowered:
        return True
    if "display power: state=off" in lowered or "mholdingdisplaywakelockssuspendblocker=false" in lowered:
        return False
    if "mwakefulness=awake" in compact or "misinteractive:true" in compact or "misinteractive=true" in compact:
        return True
    if "mwakefulness=asleep" in compact or "misinteractive:false" in compact or "misinteractive=false" in compact:
        return False
    wakefulness_lines = [line.lower() for line in output.splitlines() if "wakefulness=" in line.lower()]
    if any("awake" in line or "dreaming" in line for line in wakefulness_lines):
        return True
    if any("asleep" in line for line in wakefulness_lines):
        return False
    raise RuntimeError("Không đọc được trạng thái màn hình Pixel từ dumpsys power.")


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
    config = load_config()
    pixel_cfg = config.get("pixel", {})
    connection_mode = pixel_cfg.get("connection_mode", "usb")
    wifi_ip = pixel_cfg.get("wifi_ip", "")

    adb = pipeline.adb_command(cfg, "devices", check=False).stdout.splitlines()
    devices = [line.split()[0] for line in adb if "\tdevice" in line]
    try:
        folders, ready = list_drive_folders(), True
    except Exception:
        folders, ready = [], False
        
    return jsonify({
        "adb_device": devices[0] if devices else "", 
        "drive_root": str(drive_root()), 
        "drive_ready": ready, 
        "selected_folder": selected_folder_name(), 
        "folders": folders, 
        "operation_busy": OPERATION_LOCK.locked(),
        "connection_mode": connection_mode,
        "wifi_ip": wifi_ip
    })


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


@app.post("/api/pixel/connection")
def api_pixel_connection():
    try:
        if OPERATION_LOCK.locked():
            raise RuntimeError("Pixel đang chụp hoặc quay. Hãy đợi tác vụ hiện tại hoàn tất.")
        
        payload = request.json or {}
        connection_mode = str(payload.get("connection_mode", "usb")).strip().lower()
        wifi_ip = str(payload.get("wifi_ip", "")).strip()

        if connection_mode not in {"usb", "wifi"}:
            raise ValueError("Kiểu kết nối không hợp lệ.")

        with CONFIG_LOCK:
            config = load_config()
            config.setdefault("pixel", {})["connection_mode"] = connection_mode
            config.setdefault("pixel", {})["wifi_ip"] = wifi_ip
            save_config(config)

        cfg = settings()
        status_msg = f"Đã chuyển cấu hình sang kết nối qua {connection_mode.upper()}."
        
        if connection_mode == "wifi":
            if not wifi_ip:
                raise ValueError("Vui lòng nhập địa chỉ IP của Pixel.")
            target = f"{wifi_ip}:5555"
            add_event({"step": "wifi_connect_attempt", "message": f"Đang thử kết nối Wi-Fi đến {target}...", "ip": wifi_ip})
            res = pipeline.adb_command(cfg, "connect", target, check=False).stdout
            if "connected" in res.lower() or "already connected" in res.lower():
                status_msg = f"Kết nối Wi-Fi thành công đến {target}."
                add_event({"step": "wifi_connected", "message": status_msg, "ip": wifi_ip})
            else:
                add_event({"step": "wifi_connect_warning", "message": f"Yêu cầu kết nối Wi-Fi đã gửi: {res.strip()}", "ip": wifi_ip})
        else:
            add_event({"step": "usb_mode", "message": "Đã chuyển sang chế độ cắm dây USB."})

        return jsonify({"status": status_msg, "connection_mode": connection_mode, "wifi_ip": wifi_ip})
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/pixel/detect-ip")
def api_pixel_detect_ip():
    try:
        cfg = settings()
        # Quét danh sách thiết bị hiện có
        output = pipeline.adb_command(cfg, "devices", check=False).stdout.splitlines()
        usb_devices = []
        for line in output:
            if "\tdevice" in line:
                serial = line.split()[0]
                if ":" not in serial: # Không phải thiết bị mạng
                    usb_devices.append(serial)
                    
        if not usb_devices:
            raise RuntimeError("Không tìm thấy thiết bị Pixel đang cắm cáp USB. Hãy cắm tạm cáp USB để tự động dò IP.")
            
        target_usb = usb_devices[0]
        # Lấy IP từ thiết bị wlan0 của thiết bị usb này
        ip_output = pipeline.adb_command(cfg, "-s", target_usb, "shell", "ip addr show wlan0", check=False).stdout
        
        match = re.search(r"inet\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", ip_output)
        if not match:
            raise RuntimeError("Thiết bị Pixel đã kết nối USB nhưng không tìm thấy địa chỉ IP Wifi. Hãy kiểm tra xem Pixel đã kết nối vào cùng mạng Wifi chưa.")
            
        ip = match.group(1)
        # Kích hoạt tcpip 5555 trên thiết bị USB này luôn để người dùng đỡ phải làm thủ công!
        pipeline.adb_command(cfg, "-s", target_usb, "tcpip", "5555", check=False)
        
        add_event({"step": "ip_detected", "message": f"Đã dò tìm thấy IP của Pixel wlan0: {ip} và tự động kích hoạt chế độ không dây TCP/IP 5555.", "ip": ip})
        return jsonify({"ip": ip, "status": "Dò IP thành công."})
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


@app.post("/api/sleep-pixel")
def api_sleep_pixel():
    try:
        if OPERATION_LOCK.locked():
            raise RuntimeError("Pixel đang chụp hoặc quay. Hãy đợi tác vụ hiện tại hoàn tất.")
        cfg = settings()
        serial = adb_device_serial(cfg)
        stop_existing_scrcpy()
        sleep_pixel(cfg)
        add_event({"step": "pixel_sleep", "message": "Đã tắt màn hình Pixel và đóng scrcpy.", "adb_serial": serial})
        return jsonify({"status": "Đã tắt màn hình Pixel.", "adb_serial": serial})
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/toggle-screen")
def api_toggle_screen():
    try:
        if OPERATION_LOCK.locked():
            raise RuntimeError("Pixel đang chụp hoặc quay. Hãy đợi tác vụ hiện tại hoàn tất.")
        cfg = settings()
        serial = adb_device_serial(cfg)
        was_on = pixel_screen_is_on(cfg)
        if was_on:
            stop_existing_scrcpy()
            sleep_pixel(cfg)
            action = "off"
            message = "Đã tắt màn hình Pixel và đóng scrcpy."
            status = "Đã tắt màn hình Pixel."
        else:
            wake_pixel(cfg)
            action = "on"
            message = "Đã bật màn hình Pixel."
            status = "Đã bật màn hình Pixel."
        add_event({"step": "pixel_screen_toggle", "action": action, "message": message, "adb_serial": serial})
        return jsonify({"status": status, "screen": action, "adb_serial": serial})
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8765")), debug=False, threaded=True)
