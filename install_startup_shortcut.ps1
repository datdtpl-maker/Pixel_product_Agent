Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TaskName = "Pixel Product Agent"
$ProjectDir = "C:\Users\datdt\Documents\Codex\2026-05-27\project-n-y-nousresearch-hermes-agent"
$Launcher = Join-Path $ProjectDir "start_pixel_agent.ps1"
$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "$TaskName.lnk"

if (-not (Test-Path $Launcher)) {
    throw "Missing launcher: $Launcher"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$Launcher`""
$shortcut.WorkingDirectory = $ProjectDir
$shortcut.WindowStyle = 7
$shortcut.Description = "Starts the local Pixel Product Capture web agent at Windows logon."
$shortcut.Save()

& $Launcher

Write-Host "Created startup shortcut: $ShortcutPath"
Write-Host "Open: http://pixel-agent.test:8765 or http://127.0.0.1:8765"
