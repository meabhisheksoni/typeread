#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "==================================================================="
echo "                    Starting TypeRead..."
echo "==================================================================="

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed!"
    exit 1
fi

echo "[*] Checking dependencies..."
pip3 install -r requirements.txt --quiet

echo "[*] Launching TypeRead..."
python3 app_launcher.py
