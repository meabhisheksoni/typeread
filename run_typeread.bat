@echo off
REM ============================================================
REM TypeRead - Windows Quick Launch Script
REM ============================================================
REM Run this .bat file ONLY if you are running from the SOURCE code
REM (not from the TypeRead.exe bundled release).
REM
REM For the bundled .exe, just open TypeRead.exe directly.
REM ============================================================
echo ==================================================
echo           TypeRead Application Launcher
echo ==================================================
echo.

REM Check Python is installed
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10 or newer from https://python.org
    pause
    exit /b 1
)

echo [INFO] Installing dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

echo [INFO] Launching TypeRead...
echo ==================================================
python app_launcher.py

pause
