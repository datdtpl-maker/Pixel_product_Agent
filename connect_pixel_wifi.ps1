# Script tu dong ket noi Pixel qua Wifi
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   Pixel Drive Capture - Wi-Fi Connect Tool  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Kiem tra thiet bi dang cam cap
$devices = adb devices
$usbDevice = $devices | Where-Object { $_ -match "\tdevice$" -and $_ -notmatch ":" }

if ($usbDevice) {
    Write-Host "[+] Tim thay Pixel dang cam cap USB." -ForegroundColor Green
    Write-Host "[+] Dang tu dong lay dia chi IP Wifi cua Pixel..." -ForegroundColor Yellow
    $ipOutput = adb shell "ip addr show wlan0"
    if ($ipOutput -match "inet\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})") {
        $pixelIp = $Matches[1]
        Write-Host "[+] IP cua Pixel la: $pixelIp" -ForegroundColor Green
        Write-Host "[+] Dang kich hoat che do TCP/IP 5555 tren Pixel..." -ForegroundColor Yellow
        adb tcpip 5555 | Out-Null
        Start-Sleep -Seconds 2
        Write-Host "[+] Dang ket noi khong day..." -ForegroundColor Yellow
        $connResult = adb connect "$pixelIp:5555"
        if ($connResult -match "connected") {
            Write-Host "[SUCCESS] KET NOI KHONG DAY THANH CONG!" -ForegroundColor Green
            Write-Host "[!] Ban co the RUT CAP USB ra ngay bay gio va su dung tool khong day." -ForegroundColor Cyan
        } else {
            Write-Host "[-] Loi ket noi: $connResult" -ForegroundColor Red
        }
    } else {
        Write-Host "[-] Khong tu dong lay duoc IP. Vui long nhap IP thu cong." -ForegroundColor Yellow
        $pixelIp = Read-Host "Nhap IP cua Pixel (xem trong Settings -> Wifi)"
        if ($pixelIp) {
            adb tcpip 5555 | Out-Null
            Start-Sleep -Seconds 1
            adb connect "$pixelIp:5555"
        }
    }
} else {
    Write-Host "[i] Khong thay Pixel cam cap USB." -ForegroundColor Yellow
    Write-Host "[i] Nhap IP cua Pixel de ket noi truc tiep (neu da duoc kich hoat truoc do)." -ForegroundColor Yellow
    $pixelIp = Read-Host "Nhap IP cua Pixel (vi du: 192.168.1.18)"
    if ($pixelIp) {
        adb connect "$pixelIp:5555"
    }
}
Write-Host ""
Write-Host "Nhan phim bat ky de thoat..."
$null = [System.Console]::ReadKey($true)
