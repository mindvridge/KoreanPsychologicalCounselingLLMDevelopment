# espeak.exe 생성 스크립트 (관리자 권한 필요)
# 관리자 권한으로 PowerShell에서 실행: .\create_espeak_symlink.ps1

$espeakPath = "C:\Program Files\eSpeak NG"
$espeakNgExe = Join-Path $espeakPath "espeak-ng.exe"
$espeakExe = Join-Path $espeakPath "espeak.exe"

if (Test-Path $espeakNgExe) {
    if (-Not (Test-Path $espeakExe)) {
        Write-Host "Creating espeak.exe from espeak-ng.exe..." -ForegroundColor Yellow
        Copy-Item $espeakNgExe $espeakExe -Force
        Write-Host "Success! espeak.exe created." -ForegroundColor Green
    } else {
        Write-Host "espeak.exe already exists." -ForegroundColor Green
    }
} else {
    Write-Host "Error: espeak-ng.exe not found at $espeakNgExe" -ForegroundColor Red
    exit 1
}

Write-Host "`nTesting espeak..." -ForegroundColor Yellow
& $espeakExe --version

