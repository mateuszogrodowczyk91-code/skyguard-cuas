# =====================================================================
# SKYGUARD TACTICAL - AUTOMATIC ADB APK BUILD & DEPLOY TO PIXEL 10 PRO
# =====================================================================

$ErrorActionPreference = "Stop"

Write-Host "=== SKYGUARD ADB AUTOMATIC DEPLOYMENT ===" -ForegroundColor Cyan

# 1. Sprawdzenie połączenia ADB
Write-Host "[1/4] Sprawdzanie połączonych urządzeń Android (ADB)..." -ForegroundColor Yellow
$adbDevices = adb devices | Select-String -Pattern "device$"
if (-not $adbDevices) {
    Write-Host "[ERROR] Nie znaleziono połączonego Pixela! Włącz debugowanie USB na telefonie i podłącz go kablem USB-C." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Urządzenie wykryte!" -ForegroundColor Green

# 2. Kompilacja APK (.NET 8 Android)
Write-Host "[2/4] Kompilacja aplikacji MAUI / Android (.APK)..." -ForegroundColor Yellow
dotnet publish -f net8.0-android -c Release -p:AndroidPackageFormat=apk

$apkPath = Get-ChildItem -Path "bin\Release\net8.0-android" -Filter "*.apk" -Recurse | Select-Object -First 1

if (-not $apkPath) {
    Write-Host "[ERROR] Plik .APK nie został znaleziony w folderze wyjściowym!" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Znaleziono paczkę APK: $($apkPath.FullName)" -ForegroundColor Green

# 3. Instalacja APK na Pixelu
Write-Host "[3/4] Instalowanie aplikacji na Pixel 10 Pro..." -ForegroundColor Yellow
adb install -r $apkPath.FullName

# 4. Automatyczny autostart aplikacji
Write-Host "[4/4] Uruchamianie SKYGUARD Tactical na Pixelu..." -ForegroundColor Yellow
adb shell am start -n com.skyguard.tactical/com.skyguard.tactical.MainActivity

Write-Host "=== WDROŻENIE ZAKOŃCZONE SUKCESEM ===" -ForegroundColor Green
