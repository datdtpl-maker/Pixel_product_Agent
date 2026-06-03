@echo off
title Khoi dong Chrome Debug Port 9222
echo Dang tim kiem duong dan Google Chrome...

set "CHROME_PATH="
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%LocalAppData%\Google\Chrome\Application\chrome.exe"
)

if "%CHROME_PATH%"=="" (
    echo Khong tim thay Google Chrome tren cac thu muc mac dinh!
    echo Vui long mo Chrome bang tay voi cac tham sau:
    echo chrome.exe --remote-debugging-port=9222 --user-data-dir="%%LOCALAPPDATA%%\Google\Chrome\User Data Debug"
    pause
    exit /b
)

echo Da tim thay Chrome tai: %CHROME_PATH%
echo Dang khoi dong Chrome o che do Cua so Doc lap (App Mode) voi debug port 9222...
echo (Dieu nay giup an thanh URL, tao trai nghiem gop chung sang trong giong Widget ung dung)

start "" "%CHROME_PATH%" --app="https://chatgpt.com" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data Debug"
echo Chrome Debug App da duoc khoi dong!
exit
