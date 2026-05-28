Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TaskName = "Pixel Product Agent"
$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "$TaskName.lnk"

if (Test-Path $ShortcutPath) {
    Remove-Item -LiteralPath $ShortcutPath -Force
    Write-Host "Removed startup shortcut: $ShortcutPath"
} else {
    Write-Host "Startup shortcut not found: $ShortcutPath"
}
