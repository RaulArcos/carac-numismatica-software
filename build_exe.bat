@echo off
echo ================================================
echo Building CARAC Windows Executable
echo ================================================
echo.

echo [1/4] Installing PyInstaller...
python3.13.exe -m poetry install --with packaging
if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b %errorlevel%
)

echo.
echo [2/4] Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "CARAC.exe" del /q "CARAC.exe"

echo.
echo [3/4] Building executable with PyInstaller...
python3.13.exe -m poetry run pyinstaller carac.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b %errorlevel%
)

echo.
echo [4/4] Moving executable to root directory...
if exist "dist\CARAC.exe" (
    move "dist\CARAC.exe" "CARAC.exe"
    echo.
    echo ================================================
    echo SUCCESS! Executable created: CARAC.exe
    echo ================================================
    echo.
    echo You can now distribute CARAC.exe to any Windows computer.
    echo The executable is standalone and requires no installation.
    echo.
) else (
    echo ERROR: Executable not found in dist folder
    pause
    exit /b 1
)

echo Press any key to exit...
pause >nul

