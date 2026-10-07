@echo off
title TypeRead - Build Windows EXE
cd /d "%~dp0"

echo ===================================================================
echo               Building Standalone TypeRead.exe
echo ===================================================================

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not found on your system PATH!
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo [*] Installing build tools...
pip install pyinstaller -r requirements.txt --quiet

echo [*] Compiling TypeRead.exe...
pyinstaller --clean --noconfirm --onedir --windowed --name "TypeRead" ^
    --add-data "src/storage/schema.sql;src/storage" ^
    --add-data "src/storage/schema.sql;." ^
    app_launcher.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo ===================================================================
    echo  [SUCCESS] Build Complete!
    echo  Your executable is located at: dist\TypeRead\TypeRead.exe
    echo ===================================================================
    explorer dist\TypeRead
) else (
    echo [ERROR] PyInstaller build failed. See logs above.
)

pause
