Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Domain = "pixel-agent.test"
$Ip = "127.0.0.1"
$HostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
$Entry = "$Ip`t$Domain"

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Run this PowerShell script as Administrator."
}

$content = Get-Content -Path $HostsPath -ErrorAction Stop
if ($content -match "(^|\s)$([regex]::Escape($Domain))(\s|$)") {
    Write-Host "$Domain already exists in hosts."
} else {
    Add-Content -Path $HostsPath -Value $Entry
    Write-Host "Added: $Entry"
}

Write-Host "Open: http://$Domain`:8765"
