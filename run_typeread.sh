#!/usr/bin/env bash
# ============================================================
# TypeRead - Linux/macOS Quick Launch Script
# ============================================================
# This script installs dependencies (if missing) and launches
# the TypeRead desktop application.
# Usage: bash run_typeread.sh
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "          TypeRead Application Launcher            "
echo "=================================================="

# Check Python 3.10+
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 is not installed. Please install Python 3.10 or newer."
    exit 1
fi

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[INFO] Python version: $PYTHON_VER"

# Install dependencies if not already installed
echo "[INFO] Checking and installing dependencies..."
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r requirements.txt

# On Linux, PySide6 requires certain system libraries
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "[INFO] Linux detected. Ensuring system libraries are available..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y libegl1 libegl-mesa0 2>/dev/null || true
    elif command -v yum &>/dev/null; then
        sudo yum install -y mesa-libEGL 2>/dev/null || true
    fi
fi

# Launch TypeRead
echo "[INFO] Starting TypeRead..."
echo "=================================================="
python3 app_launcher.py
