Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Port = 8765
$LogDir = Join-Path $ProjectDir "logs"
$LogFile = Join-Path $LogDir "pixel-agent.log"
$ErrorLogFile = Join-Path $LogDir "pixel-agent-error.log"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
Set-Location $ProjectDir

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    try {
        "[$(Get-Date -Format s)] Pixel Agent already listening on port $Port" | Add-Content -Path $LogFile -ErrorAction Stop
    } catch {
        Write-Host "Pixel Agent already listening on port $Port"
    }
    exit 0
}

$python = (Get-Command python -ErrorAction Stop).Source
$arguments = ".\web_app.py"

try {
    "[$(Get-Date -Format s)] Starting Pixel Agent on port $Port" | Add-Content -Path $LogFile -ErrorAction Stop
} catch {
    Write-Host "Starting Pixel Agent on port $Port"
}

# PowerShell Start-Process fails when the parent environment contains both
# Path and PATH entries. Normalize them before launching the hidden server.
$processPath = $env:Path
[Environment]::SetEnvironmentVariable("Path", $null, "Process")
[Environment]::SetEnvironmentVariable("PATH", $null, "Process")
[Environment]::SetEnvironmentVariable("Path", $processPath, "Process")

Start-Process -FilePath $python `
    -ArgumentList $arguments `
    -WorkingDirectory $ProjectDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError $ErrorLogFile
