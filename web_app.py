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

import base64
import requests
from concurrent.futures import ThreadPoolExecutor

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
    input, select, textarea {
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
    body.theme-light input, body.theme-light select, body.theme-light textarea {
      background: #fff;
      border-color: #cbd5e1;
      color: var(--text);
    }
    input:focus, select:focus, textarea:focus {
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
    /* Poster Editor Styles */
    .spinner {
      border: 4px solid var(--soft);
      border-top-color: var(--brand);
      border-radius: 50%;
      width: 48px;
      height: 48px;
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    .thumbnail-wrapper {
      position: relative;
      width: 100%;
      aspect-ratio: 1;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid var(--panel-border);
      background: var(--soft);
    }
    .thumbnail-wrapper img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .thumbnail-wrapper .remove-btn {
      position: absolute;
      top: 4px;
      right: 4px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: var(--danger);
      color: #fff;
      display: grid;
      place-items: center;
      font-size: 11px;
      font-weight: bold;
      cursor: pointer;
      border: none;
      padding: 0;
      min-height: auto;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
      transition: background 0.2s;
    }
    .thumbnail-wrapper .remove-btn:hover {
      background: var(--danger-hover);
    }
    .poster-card {
      position: relative;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid var(--panel-border);
      background: var(--soft);
      box-shadow: var(--shadow);
      transition: all 0.3s;
    }
    .poster-card:hover {
      transform: translateY(-4px);
      border-color: rgba(59,130,246,0.3);
    }
    .poster-card img {
      width: 100%;
      height: auto;
      aspect-ratio: inherit;
      display: block;
      object-fit: contain;
      background: #000;
    }
    .poster-card .card-actions {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 100%);
      padding: 24px 16px 16px;
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      opacity: 0;
      transition: opacity 0.3s;
    }
    .poster-card:hover .card-actions {
      opacity: 1;
    }
    .quantity-selector button {
      min-height: 38px;
      padding: 4px;
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
  <main class="main" style="display: flex; flex-direction: column;">
    <div id="captureDashboard" style="display: block; width: 100%;">
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
          <button class="secondary" onclick="showPosterDashboard()" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%); border-color: rgba(168, 85, 247, 0.3);">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #a855f7;"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
            Tạo Poster AI
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
    </div>

    <!-- AI Poster Generator Tab -->
    <div id="posterDashboard" style="display: none; flex-direction: column; width: 100%;">
      <header class="topbar">
        <div style="display: flex; align-items: center; gap: 16px;">
          <button class="ghost" onclick="showCaptureDashboard()" style="min-height: 38px; padding: 8px 12px;" title="Quay lại Bảng điều khiển">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
          </button>
          <h2>Tạo ảnh đa năng</h2>
        </div>
        <div class="actions">
          <div style="display: flex; align-items: center; gap: 8px; background: var(--soft); border: 1px solid var(--panel-border); padding: 8px 16px; border-radius: 99px; font-weight: 700; font-size: 13px; color: var(--text);">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
            GPT-4o + GPT Image 1.5
          </div>
        </div>
      </header>
      
      <div class="content" style="padding: 24px; display: grid; grid-template-columns: 340px minmax(0, 1fr); gap: 24px; width: 100%;">
        <!-- Left Sidebar: Configurations -->
        <aside class="panel" style="display: flex; flex-direction: column; gap: 20px; padding: 24px; height: fit-content;">
          <!-- Image Dropzone -->
          <div>
            <label>Tải lên hình ảnh (Tối đa 4)</label>
            <div id="imageDropzone" onclick="document.getElementById('posterFiles').click()" style="border: 2px dashed var(--panel-border); border-radius: 12px; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; transition: all 0.3s; background: rgba(0,0,0,0.12);">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--muted); margin-bottom: 8px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
              <span style="font-size: 12px; color: var(--muted); font-weight: 500; text-align: center; padding: 0 10px;">Bấm hoặc Kéo thả ảnh sản phẩm</span>
              <input type="file" id="posterFiles" multiple accept="image/*" style="display: none;" onchange="handlePosterFiles(this.files)">
            </div>
            <div id="uploadedThumbnails" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 12px;"></div>
          </div>
          
          <!-- Prompt input -->
          <div>
            <label for="posterPrompt">Yêu cầu tạo ảnh mới</label>
            <textarea id="posterPrompt" placeholder="Vui lòng mô tả ý tưởng poster của bạn...&#10;(Ví dụ: Đặt sản phẩm này trên mặt cát, có sóng biển vỗ nhẹ bên cạnh, ánh sáng tự nhiên)" style="height: 110px; resize: none; font-size: 13px; line-height: 1.4;" oninput="updatePromptCount()"></textarea>
            <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 11px; color: var(--muted);">
              <span onclick="insertPromptTemplate()" style="cursor: pointer; color: var(--brand); font-weight: 700;">✨ Dùng mẫu prompt</span>
              <span id="promptCharCount">0/1000</span>
            </div>
          </div>
          
          <!-- Quantity -->
          <div>
            <label>Số lượng tạo</label>
            <div class="quantity-selector" style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px;">
              <button type="button" class="select-btn" id="btnQty1" onclick="selectQuantity(this, 1)">1</button>
              <button type="button" class="secondary select-btn" onclick="selectQuantity(this, 2)">2</button>
              <button type="button" class="secondary select-btn" onclick="selectQuantity(this, 4)">4</button>
              <button type="button" class="secondary select-btn" onclick="selectQuantity(this, 6)">6</button>
              <button type="button" class="secondary select-btn" onclick="selectQuantity(this, 9)">9</button>
            </div>
            <input type="hidden" id="posterQuantity" value="1">
          </div>
          
          <!-- Aspect ratio -->
          <div>
            <label for="posterSize">Tỷ lệ kích thước</label>
            <select id="posterSize" style="font-size: 13px;">
              <option value="1024x1024">Square (1:1) - 1024x1024 px</option>
              <option value="1024x1792">Portrait (9:16) - 1024x1792 px</option>
              <option value="1792x1024">Landscape (16:9) - 1792x1024 px</option>
            </select>
          </div>

          <!-- API Settings -->
          <div>
            <label for="openaiKey">OpenAI API Key</label>
            <div class="field-action" style="grid-template-columns: minmax(0, 1fr) auto auto; gap: 8px;">
              <input type="password" id="openaiKey" placeholder="sk-proj-..." style="font-size: 12px; min-height: 38px;">
              <button type="button" class="secondary" onclick="saveOpenAIConfigBtn()" style="min-height: 38px; padding: 0 12px;">Lưu</button>
              <button type="button" class="secondary" id="btnCheckAPI" onclick="checkAPIKey()" style="min-height: 38px; padding: 0 12px;">Kiểm tra</button>
            </div>
          </div>

          <!-- Export Folder -->
          <div>
            <label for="posterExportDir">Thư mục xuất hình</label>
            <div class="field-action">
              <input id="posterExportDir" placeholder="Mặc định: Thư mục Drive hiện tại" style="font-size: 12px; min-height: 38px;">
              <button type="button" class="secondary" onclick="browseExportDirectory()" style="min-height: 38px; padding: 0 16px;">Chọn</button>
            </div>
          </div>
          
          <!-- Submit button -->
          <button class="btn-capture" id="btnGeneratePoster" onclick="generatePoster()" style="width: 100%; font-size: 14px; padding: 12px; margin-top: 10px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
            Tạo Poster AI
          </button>
        </aside>
        
        <!-- Right Main Panel: Generation Result -->
        <main class="panel" style="display: flex; flex-direction: column; min-height: 580px; padding: 24px; width: 100%;">
          <div class="panel-head" style="padding: 0 0 20px 0; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; align-items: center;">
            <div>
              <h3 style="font-size: 20px; font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif;">Poster Quảng Cáo</h3>
              <p style="margin-top: 4px; color: var(--muted); font-size: 13px;">Giao diện hiển thị poster tạo tự động bằng AI.</p>
            </div>
            <div id="generationStatus" style="display: none; align-items: center; gap: 8px;">
              <span class="badge warn" id="statusBadge" style="padding: 6px 12px;">Đang chuẩn bị...</span>
            </div>
          </div>
          
          <div class="panel-body" style="flex: 1; padding: 24px 0 0 0; display: flex; flex-direction: column; justify-content: center; align-items: center; width: 100%;">
            <!-- Initial view -->
            <div id="posterPlaceholder" style="display: flex; flex-direction: column; align-items: center; text-align: center; color: var(--muted); max-width: 440px; margin: auto;">
              <div style="width: 80px; height: 80px; border-radius: 50%; background: var(--soft); border: 1px solid var(--panel-border); display: grid; place-items: center; margin-bottom: 20px; box-shadow: var(--shadow);">
                <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--brand);"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
              </div>
              <h4 style="font-size: 16px; color: #fff; margin: 0 0 8px 0; font-family: 'Plus Jakarta Sans', sans-serif;">Chưa có ảnh poster nào được tạo</h4>
              <p style="font-size: 13px; line-height: 1.5; margin: 0;">Nhập yêu cầu và tải lên ảnh sản phẩm thô ở cột bên trái, sau đó bấm nút "Tạo Poster AI" để bắt đầu thiết kế.</p>
            </div>
            
            <!-- Loading indicator -->
            <div id="posterLoading" style="display: none; flex-direction: column; align-items: center; justify-content: center; gap: 18px; margin: auto;">
              <div class="spinner"></div>
              <div style="text-align: center;">
                <h4 style="font-size: 15px; color: #fff; margin: 0 0 6px 0; font-family: 'Plus Jakarta Sans', sans-serif;" id="loadingText">Đang xử lý tạo ảnh...</h4>
                <p style="font-size: 12px; color: var(--muted); margin: 0;">Quá trình phân tích Vision và vẽ tranh thường mất 10 - 20 giây.</p>
              </div>
            </div>
            
            <!-- Grid displaying generated images -->
            <div id="posterGrid" style="display: none; width: 100%; grid-template-columns: repeat(2, 1fr); gap: 24px;"></div>
          </div>
          
          <!-- Bottom disclaimer -->
          <div style="border-top: 1px solid var(--line); padding-top: 16px; margin-top: 24px; font-size: 11px; color: var(--muted); line-height: 1.5; text-align: center;">
            Miễn trừ trách nhiệm: Tất cả nội dung được tạo ra bởi dịch vụ này đều được tạo tự động bằng AI và chỉ mang tính chất tham khảo. Chúng tôi không đảm bảo tính chính xác, đầy đủ hoặc tính ứng dụng của nội dung.
          </div>
        </main>
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
  // Poster Creator JS
  let posterImages = []; // Mảng chứa base64 của ảnh upload
  
  function showPosterDashboard() {
    document.getElementById("captureDashboard").style.display = "none";
    document.getElementById("posterDashboard").style.display = "flex";
    // Tải cấu hình OpenAI từ backend lên UI
    loadOpenAIConfig();
  }
  
  function showCaptureDashboard() {
    document.getElementById("posterDashboard").style.display = "none";
    document.getElementById("captureDashboard").style.display = "block";
  }
  
  function handlePosterFiles(files) {
    const limit = 4;
    const currentCount = posterImages.length;
    const remaining = limit - currentCount;
    const filesToProcess = Array.from(files).slice(0, remaining);
    
    filesToProcess.forEach(file => {
      const reader = new FileReader();
      reader.onload = function(e) {
        posterImages.push({
          name: file.name,
          base64: e.target.result
        });
        renderThumbnails();
      };
      reader.readAsDataURL(file);
    });
  }
  
  function renderThumbnails() {
    const container = document.getElementById("uploadedThumbnails");
    container.innerHTML = "";
    
    posterImages.forEach((img, idx) => {
      const wrapper = document.createElement("div");
      wrapper.className = "thumbnail-wrapper";
      wrapper.innerHTML = `
        <img src="${img.base64}" alt="${escapeHtml(img.name)}">
        <button class="remove-btn" onclick="removeUploadedImage(${idx})">×</button>
      `;
      container.appendChild(wrapper);
    });
    
    // Cập nhật nhãn đếm ảnh
    const label = document.querySelector("#posterDashboard label");
    label.textContent = `Tải lên hình ảnh (Tối đa 4) - Đã chọn ${posterImages.length}/4`;
  }
  
  function removeUploadedImage(idx) {
    posterImages.splice(idx, 1);
    renderThumbnails();
  }
  
  function updatePromptCount() {
    const prompt = document.getElementById("posterPrompt").value;
    document.getElementById("promptCharCount").textContent = `${prompt.length}/1000`;
  }
  
  function selectQuantity(btn, qty) {
    document.getElementById("posterQuantity").value = qty;
    document.querySelectorAll(".quantity-selector .select-btn").forEach(b => {
      b.classList.add("secondary");
    });
    btn.classList.remove("secondary");
  }
  
  const promptTemplates = [
    "Vui lòng tạo một poster quảng cáo sang trọng cho sản phẩm này, đặt trên một bệ đá cẩm thạch trắng, xung quanh có các giọt nước tinh khiết lấp lánh, ánh sáng studio studio softbox rực rỡ, nền màu gradient xanh dương mát mẻ, phong cách chuyên nghiệp, ảnh quảng cáo mỹ phẩm thương mại.",
    "Tạo poster quảng cáo thương mại cho sản phẩm, bối cảnh thiên nhiên tự nhiên với các lá trà xanh tươi mát xung quanh, ánh nắng tự nhiên nhẹ nhàng chiếu qua kẽ lá, hậu cảnh bokeh rừng xanh mướt, phong cách organic sạch sẽ, quảng cáo sản phẩm tự nhiên.",
    "Poster quảng cáo sản phẩm phong cách tương lai huyền ảo, đặt sản phẩm trên đĩa bay hologram phát sáng neon màu tím và xanh lam, nền công nghệ cyber hiện đại mờ ảo, khói huyền ảo bay nhẹ, phong cách 3D render cực kỳ sắc nét.",
    "Thiết kế poster quảng cáo phong cách tối giản (minimalism) cho sản phẩm, đặt trên một khối gỗ thô mộc mạc, nền trơn màu be ấm áp, ánh sáng mặt trời tự nhiên tạo bóng đổ dài nghệ thuật, phong cách đơn giản, tinh tế, trang nhã."
  ];
  let currentTemplateIdx = 0;
  
  function insertPromptTemplate() {
    document.getElementById("posterPrompt").value = promptTemplates[currentTemplateIdx];
    updatePromptCount();
    currentTemplateIdx = (currentTemplateIdx + 1) % promptTemplates.length;
  }
  
  async function checkAPIKey() {
    const key = document.getElementById("openaiKey").value.trim();
    if (!key) {
      alert("Vui lòng nhập API Key trước khi kiểm tra.");
      return;
    }
    
    const btn = document.getElementById("btnCheckAPI");
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Đang check...";
    
    try {
      const r = await fetch("/api/openai/check", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({api_key: key})
      });
      const d = await r.json();
      
      if (d.valid) {
        // Tự động lưu khi check thành công
        await saveOpenAIConfig();
        let msg = "Kết nối API Key thành công!\n\n";
        msg += `1. GPT-4o / GPT-4o-mini: ${d.has_gpt4o ? "Sẵn sàng ✅" : "Không có quyền ❌"}\n`;
        msg += `2. GPT-image-1.5: ${d.has_dalle3 ? "Sẵn sàng ✅" : "Không có quyền ❌"}\n\n`;
        if (!d.has_dalle3) {
          msg += "⚠️ CẢNH BÁO: Tài khoản của bạn gọi được GPT-4o nhưng mô hình gpt-image-1.5 bị OpenAI báo không tồn tại. Vui lòng kiểm tra xem bạn đã nạp đủ $5 (lên Tier 1) chưa hoặc xem trong mục Settings -> Projects -> Limits/Models trên trang OpenAI xem model gpt-image-1.5 có bị tắt (disabled) không.";
        } else {
          msg += "🎉 Tài khoản của bạn đã đầy đủ quyền và sẵn sàng hoạt động!";
        }
        alert(msg);
      } else {
        alert("Lỗi kết nối API: " + d.message);
      }
    } catch(e) {
      alert("Lỗi kiểm tra API: " + (e.message || JSON.stringify(e)));
    } finally {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  }

  async function loadOpenAIConfig() {
    try {
      const r = await fetch("/api/openai/config");
      const d = await r.json();
      if (d.api_key) {
        document.getElementById("openaiKey").value = d.api_key;
      }
      if (d.export_dir) {
        document.getElementById("posterExportDir").value = d.export_dir;
      }
    } catch(e) {
      console.error(e);
    }
  }
  
  async function saveOpenAIConfig() {
    const key = document.getElementById("openaiKey").value.trim();
    const dir = document.getElementById("posterExportDir").value.trim();
    await fetch("/api/openai/config", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({api_key: key, export_dir: dir})
    });
  }
  
  async function saveOpenAIConfigBtn() {
    try {
      await saveOpenAIConfig();
      alert("Đã lưu API Key thành công!");
    } catch(e) {
      alert("Lỗi lưu API Key: " + (e.message || JSON.stringify(e)));
    }
  }
  
  async function browseExportDirectory() {
    try {
      const r = await fetch("/api/utils/select-directory", { method: "POST" });
      const d = await r.json();
      if (d.directory) {
        document.getElementById("posterExportDir").value = d.directory;
        await saveOpenAIConfig();
      }
    } catch(e) {
      alert("Không thể mở hộp thoại chọn thư mục: " + (e.error || e.message || JSON.stringify(e)));
    }
  }
  
  async function generatePoster() {
    const prompt = document.getElementById("posterPrompt").value.trim();
    const key = document.getElementById("openaiKey").value.trim();
    
    if (!key) {
      alert("Vui lòng cấu hình OpenAI API Key ở mục tương ứng trước khi tạo.");
      return;
    }
    if (!prompt) {
      alert("Vui lòng nhập yêu cầu tạo ảnh mới.");
      return;
    }
    
    // Lưu cấu hình tự động
    await saveOpenAIConfig();
    
    // Đổi trạng thái UI sang Loading
    document.getElementById("posterPlaceholder").style.display = "none";
    document.getElementById("posterGrid").style.display = "none";
    document.getElementById("posterLoading").style.display = "flex";
    document.getElementById("generationStatus").style.display = "flex";
    
    const qty = Number(document.getElementById("posterQuantity").value);
    const size = document.getElementById("posterSize").value;
    
    const statusText = document.getElementById("loadingText");
    const statusBadge = document.getElementById("statusBadge");
    
    try {
      if (posterImages.length > 0) {
        statusText.innerHTML = "Đang gửi ảnh sản phẩm thô lên GPT-4o để phân tích bối cảnh...";
        statusBadge.innerHTML = "GPT-4o Vision đang xử lý";
      } else {
        statusText.innerHTML = "Đang kết nối API OpenAI để tạo ảnh...";
        statusBadge.innerHTML = "gpt-image-1.5 đang vẽ";
      }
      
      const payload = {
        prompt: prompt,
        quantity: qty,
        size: size,
        images: posterImages.map(img => img.base64)
      };
      
      // Chạy API gọi AI tạo ảnh
      const r = await fetch("/api/poster/generate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      const d = await r.json();
      
      if (!r.ok) {
        throw d;
      }
      
      renderPosterGrid(d.images, size);
      
    } catch(e) {
      alert("Lỗi tạo ảnh: " + (e.error || e.message || JSON.stringify(e)));
      document.getElementById("posterPlaceholder").style.display = "flex";
      document.getElementById("posterLoading").style.display = "none";
      document.getElementById("generationStatus").style.display = "none";
    }
  }
  
  function renderPosterGrid(images, size) {
    document.getElementById("posterLoading").style.display = "none";
    document.getElementById("generationStatus").style.display = "none";
    
    const grid = document.getElementById("posterGrid");
    grid.innerHTML = "";
    grid.style.display = "grid";
    
    // Tùy chỉnh tỷ lệ thẻ dựa theo kích thước
    let aspect = "1/1";
    if (size === "1024x1792") aspect = "9/16";
    else if (size === "1792x1024") aspect = "16/9";
    
    images.forEach((imgUrl, idx) => {
      const card = document.createElement("div");
      card.className = "poster-card";
      card.style.aspectRatio = aspect;
      card.innerHTML = `
        <img src="${imgUrl}" alt="Poster AI ${idx + 1}" style="aspect-ratio: ${aspect};">
        <div class="card-actions">
          <button class="ghost" onclick="downloadPosterDirect('${imgUrl}', ${idx + 1})" style="min-height: 32px; padding: 4px 8px; font-size: 12px; background: rgba(0,0,0,0.6);">
            📥 Tải về máy
          </button>
          <button onclick="savePosterToDrive('${imgUrl}', ${idx + 1})" style="min-height: 32px; padding: 4px 8px; font-size: 12px;">
            💾 Lưu vào Drive
          </button>
        </div>
      `;
      grid.appendChild(card);
    });
  }
  
  async function savePosterToDrive(url, idx) {
    try {
      // Gọi API backend tải ảnh và lưu
      const response = await fetch("/api/poster/save", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          image_url: url,
          filename: `poster_ai_${new Date().strftime("%Y%m%d_%H%M%S")}_${idx}.png`
        })
      });
      const d = await response.json();
      if (!response.ok) throw d;
      alert(`Đã lưu poster thành công vào thư mục: ${d.saved_path}`);
    } catch(e) {
      alert("Lỗi lưu ảnh: " + (e.error || e.message || JSON.stringify(e)));
    }
  }

  function downloadPosterDirect(url, idx) {
    const a = document.createElement("a");
    a.href = url;
    a.target = "_blank";
    a.download = `poster_ai_${idx}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
  
  Date.prototype.strftime = function(format) {
    const o = {
      "Y+": this.getFullYear(),
      "m+": this.getMonth() + 1,
      "d+": this.getDate(),
      "H+": this.getHours(),
      "M+": this.getMinutes(),
      "S+": this.getSeconds()
    };
    let fmt = format;
    for (let k in o) {
      if (new RegExp("(" + k + ")").test(fmt)) {
        const val = String(o[k]);
        fmt = fmt.replace(RegExp.$1, (RegExp.$1.length === 1) ? val : val.padStart(RegExp.$1.length, "0"));
      }
    }
    return fmt;
  };

  initTheme();
  refresh();
</script>
</body>
</html>
"""


def settings() -> pipeline.Settings:
    pipeline.load_dotenv(ROOT)
    cfg = pipeline.load_settings(CONFIG_PATH)
    try:
        cfg.adb_serial = adb_device_serial(cfg)
    except Exception:
        pass
    return cfg


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
        
        # Nếu có các kết nối mạng khác đang tồn tại không khớp với IP mục tiêu, ngắt kết nối chúng
        network_devices = [d for d in devices if ":" in d and d != target_serial]
        if network_devices:
            for nd in network_devices:
                pipeline.adb_command(cfg, "disconnect", nd, check=False)
            # Quét lại danh sách sau khi dọn dẹp
            output = pipeline.adb_command(cfg, "devices", check=False).stdout.splitlines()
            devices = [line.split()[0] for line in output if "\tdevice" in line]
            
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
        
    current_device = cfg.adb_serial if cfg.adb_serial else (devices[0] if devices else "")
        
    return jsonify({
        "adb_device": current_device, 
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


@app.post("/api/utils/select-directory")
def api_select_directory():
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Tạo cửa sổ gốc ẩn
        root = tk.Tk()
        root.withdraw()
        # Đưa lên phía trước
        root.attributes('-topmost', True)
        
        selected_dir = filedialog.askdirectory(title="Chọn thư mục xuất hình")
        root.destroy()
        
        if selected_dir:
            return jsonify({"directory": os.path.normpath(selected_dir)})
        else:
            return jsonify({"directory": ""})
    except Exception as exc:
        return error_response(exc, 500)


@app.post("/api/openai/check")
def api_openai_check():
    try:
        payload = request.json or {}
        api_key = str(payload.get("api_key", "")).strip()
        if not api_key:
            raise ValueError("Vui lòng cung cấp API Key để kiểm tra.")
            
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        has_gpt4o = False
        try:
            models_data = client.models.list()
            model_ids = [m.id for m in models_data.data]
            has_gpt4o = "gpt-4o" in model_ids or "gpt-4o-mini" in model_ids
        except Exception as e:
            return jsonify({
                "valid": False,
                "message": f"API Key không hợp lệ hoặc tài khoản hết tiền: {e}"
            })
            
        has_dalle3 = False
        dalle3_error_msg = ""
        try:
            client.images.generate(
                model="gpt-image-1.5",
                prompt="",
                n=1,
                size="1024x1024"
            )
        except Exception as e:
            err_str = str(e)
            if "does not exist" in err_str:
                has_dalle3 = False
                dalle3_error_msg = "Mô hình gpt-image-1.5 bị khóa hoặc chưa được cấp quyền (tài khoản Tier 0 hoặc bị tắt trong Project)."
            else:
                has_dalle3 = True
                
        return jsonify({
            "valid": True,
            "has_gpt4o": has_gpt4o,
            "has_dalle3": has_dalle3,
            "dalle3_msg": dalle3_error_msg or "Sẵn sàng hoạt động ✅"
        })
    except Exception as exc:
        return jsonify({
            "valid": False,
            "message": str(exc)
        })


@app.get("/api/openai/config")
def api_openai_config_get():
    config = load_config()
    openai_cfg = config.get("openai", {})
    return jsonify({
        "api_key": openai_cfg.get("api_key", ""),
        "export_dir": openai_cfg.get("export_dir", "")
    })


@app.post("/api/openai/config")
def api_openai_config_post():
    try:
        payload = request.json or {}
        api_key = str(payload.get("api_key", "")).strip()
        export_dir = str(payload.get("export_dir", "")).strip()
        
        with CONFIG_LOCK:
            config = load_config()
            openai_cfg = config.setdefault("openai", {})
            openai_cfg["api_key"] = api_key
            openai_cfg["export_dir"] = export_dir
            save_config(config)
            
        return jsonify({"status": "Đã lưu cấu hình OpenAI."})
    except Exception as exc:
        return error_response(exc, 400)


@app.post("/api/poster/generate")
def api_poster_generate():
    try:
        payload = request.json or {}
        user_prompt = str(payload.get("prompt", "")).strip()
        quantity = max(1, min(int(payload.get("quantity") or 4), 9))
        size = str(payload.get("size", "1024x1024")).strip()
        images = payload.get("images", []) # Mảng chứa base64
        
        config = load_config()
        api_key = config.get("openai", {}).get("api_key", "").strip()
        if not api_key:
            raise ValueError("Chưa cấu hình OpenAI API Key.")
            
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # 1. Nếu có ảnh tải lên, dùng GPT-4o Vision để phân tích và sinh prompt chi tiết
        final_prompt = user_prompt
        if images:
            # Lấy ảnh đầu tiên (hoặc phân tích các ảnh)
            # GPT-4o Vision hỗ trợ gửi ảnh dưới dạng base64 qua data URL
            message_content = [
                {
                    "type": "text",
                    "text": (
                        "You are an expert product advertising poster designer. "
                        "Analyze the raw product image(s) provided (shape, color, label, brand) "
                        "and combine it with the user's background request: \"" + user_prompt + "\". "
                        "Write a highly descriptive, professional English prompt for DALL-E 3 "
                        "to generate a stunning, realistic commercial advertising poster featuring this exact product in the requested setting. "
                        "Describe the product in detail so DALL-E 3 can recreate it accurately, "
                        "along with premium studio lighting, soft shadows, and commercial photography style. "
                        "Only output the raw English prompt for DALL-E 3, nothing else."
                    )
                }
            ]
            
            for base64_data in images[:4]: # Giới hạn tối đa 4 ảnh
                # Lọc bỏ tiền tố data:image/png;base64, nếu có
                if "," in base64_data:
                    base64_data = base64_data.split(",", 1)[1]
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_data}"
                    }
                })
                
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": message_content}],
                max_tokens=500
            )
            final_prompt = response.choices[0].message.content.strip()
            # Log prompt đã tối ưu
            add_event({"step": "poster_gpt_prompt", "message": f"GPT-4o Vision đã tạo prompt vẽ tranh chi tiết: {final_prompt}"})

        # 2. Gọi gpt-image-1.5 để tạo ảnh poster
        # gpt-image-1.5 hỗ trợ tạo 1 ảnh mỗi lần gọi (n=1). Chúng ta sẽ dùng ThreadPoolExecutor để chạy song song.
        def generate_single_image():
            response = client.images.generate(
                model="gpt-image-1.5",
                prompt=final_prompt,
                size=size,
                quality="medium", # Sử dụng 'medium' để tiết kiệm chi phí theo yêu cầu người dùng
                n=1
            )
            return response.data[0].url

        add_event({"step": "poster_generating", "message": f"Đang kết nối gpt-image-1.5 để tạo {quantity} ảnh poster với kích thước {size}..."})
        
        urls = []
        with ThreadPoolExecutor(max_workers=min(quantity, 4)) as executor:
            futures = [executor.submit(generate_single_image) for _ in range(quantity)]
            for fut in futures:
                try:
                    urls.append(fut.result())
                except Exception as e:
                    # Nếu có lỗi khi tạo 1 ảnh lẻ, log lại và bỏ qua hoặc ném lỗi nếu tất cả đều lỗi
                    add_event({"step": "error", "message": f"Lỗi tạo ảnh đơn lẻ: {e}"})
                    
        if not urls:
            raise RuntimeError("Tất cả các lượt gọi API gpt-image-1.5 đều thất bại. Hãy kiểm tra kết nối API Key và quota tài khoản.")
            
        add_event({"step": "poster_done", "message": f"Đã tạo thành công {len(urls)} ảnh poster quảng cáo từ AI."})
        return jsonify({"images": urls})
        
    except Exception as exc:
        add_event({"step": "error", "message": str(exc)})
        return error_response(exc, 400)


@app.post("/api/poster/save")
def api_poster_save():
    try:
        payload = request.json or {}
        image_url = str(payload.get("image_url", "")).strip()
        filename = str(payload.get("filename", "")).strip()
        
        if not image_url or not filename:
            raise ValueError("Thiếu URL ảnh hoặc tên file.")
            
        config = load_config()
        export_dir = config.get("openai", {}).get("export_dir", "").strip()
        
        target_folder = None
        if export_dir:
            path = Path(export_dir).expanduser()
            if path.exists() and path.is_dir():
                target_folder = path
                
        if not target_folder:
            # Mặc định lưu vào thư mục Drive hiện tại đang chọn
            try:
                target_folder = selected_drive_folder()
            except Exception:
                # Nếu chưa chọn thư mục, lưu vào drive_root_dir
                target_folder = drive_root()
                
        if not target_folder.exists():
            target_folder.mkdir(parents=True, exist_ok=True)
            
        dest_path = target_folder / filename
        
        # Tải ảnh từ OpenAI URL về
        r = requests.get(image_url, timeout=30)
        r.raise_for_status()
        
        dest_path.write_bytes(r.content)
        
        add_event({"step": "poster_saved", "message": f"Đã lưu poster thành công vào thư mục: {dest_path}", "file": str(dest_path)})
        return jsonify({"status": "Lưu poster thành công.", "saved_path": str(dest_path)})
        
    except Exception as exc:
        add_event({"step": "error", "message": str(exc)})
        return error_response(exc, 400)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8765")), debug=False, threaded=True)
