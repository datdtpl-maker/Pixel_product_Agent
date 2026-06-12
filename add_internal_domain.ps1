Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Domain = "mcp-shopee-khai-hoan"
$Aliases = @($Domain, "mcp-shopee-khai-hoan.test")
$OldDomains = @("pixel-agent.test", "pixel-drive-capture", "pixel-drive-capture.test")
$Ip = "127.0.0.1"
$HostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Run this PowerShell script as Administrator."
}

$content = @(Get-Content -Path $HostsPath -ErrorAction Stop)
$updated = $content
foreach ($Old in $OldDomains) {
    $beforeCount = $updated.Count
    $updated = @($updated | Where-Object { $_ -notmatch "(^|\s)$([regex]::Escape($Old))(\s|$)" })
    if ($updated.Count -ne $beforeCount) {
        Write-Host "Removed old domain: $Old"
    }
}
if ($updated.Count -ne $content.Count) {
    Set-Content -Path $HostsPath -Value $updated
    $content = $updated
}
foreach ($Alias in $Aliases) {
    $Entry = "$Ip`t$Alias"
    if ($content -match "(^|\s)$([regex]::Escape($Alias))(\s|$)") {
        Write-Host "$Alias already exists in hosts."
    } else {
        Add-Content -Path $HostsPath -Value $Entry
        Write-Host "Added: $Entry"
        $content += $Entry
    }
}

Write-Host "Open: http://$Domain`:8765"
