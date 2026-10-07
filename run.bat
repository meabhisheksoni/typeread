@echo off
title TypeRead - Interactive Reading and Typing
cd /d "%~dp0"

echo ===================================================================
echo                     Starting TypeRead...
echo ===================================================================

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not found on your system PATH!
    echo Please install Python 3.11+ from https://python.org and check
    echo 'Add Python to PATH' during installation.
    pause
    exit /b 1
)

echo [*] Checking dependencies...
pip install -r requirements.txt --quiet

echo [*] Launching TypeRead Desktop Application...
start "" python app_launcher.py

exit /b 0
