Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Building CARAC Windows Executable" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Installing PyInstaller..." -ForegroundColor Yellow
python3.13.exe -m poetry install --with packaging
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install PyInstaller" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[2/4] Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "CARAC.exe") { Remove-Item -Force "CARAC.exe" }

Write-Host ""
Write-Host "[3/4] Building executable with PyInstaller..." -ForegroundColor Yellow
python3.13.exe -m poetry run pyinstaller carac.spec --clean --noconfirm
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[4/4] Moving executable to root directory..." -ForegroundColor Yellow
if (Test-Path "dist\CARAC.exe") {
    Move-Item "dist\CARAC.exe" "CARAC.exe" -Force
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "SUCCESS! Executable created: CARAC.exe" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now distribute CARAC.exe to any Windows computer." -ForegroundColor White
    Write-Host "The executable is standalone and requires no installation." -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "ERROR: Executable not found in dist folder" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"

