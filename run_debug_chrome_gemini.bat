@echo off
title Khoi dong Chrome Debug Port 9223
echo Dang tim kiem duong dan Google Chrome cho Gemini...

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
    echo chrome.exe --remote-debugging-port=9223 --user-data-dir="%%LOCALAPPDATA%%\Google\Chrome\User Data Debug Gemini"
    pause
    exit /b
)

echo Da tim thay Chrome tai: %CHROME_PATH%
echo Dang khoi dong Chrome Gemini o che do Cua so Doc lap (App Mode) voi debug port 9223...

start "" "%CHROME_PATH%" --app="https://gemini.google.com" --remote-debugging-port=9223 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data Debug Gemini"
echo Chrome Gemini Debug App da duoc khoi dong!
exit
