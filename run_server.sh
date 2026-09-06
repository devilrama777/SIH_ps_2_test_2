#!/usr/bin/env bash
set -e

echo "======================================================================"
echo "  CIL Local AI Report Generator -- Processing Service (Linux/macOS)"
echo "======================================================================"

if [ -f ".venv/bin/python" ]; then
    PYTHON_EXE=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_EXE="python3"
else
    echo "[ERROR] Python 3.11+ is required but was not found."
    exit 1
fi

echo "Starting server on 127.0.0.1:8765 (Air-gapped / Local Loopback only)..."
"$PYTHON_EXE" -m apps.processing.server
