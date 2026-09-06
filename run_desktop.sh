#!/usr/bin/env bash
set -e

echo "======================================================================"
echo "  CIL Local AI Report Generator -- Starting Platform (Linux/macOS)"
echo "======================================================================"

# 1. Locate Python
if [ -f ".venv/bin/python" ]; then
    PYTHON_EXE=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_EXE="python3"
else
    echo "[ERROR] Python 3.11+ is required but was not found."
    exit 1
fi

# 2. Pre-flight Environment Diagnostics
echo "[*] Running pre-flight environment diagnostics..."
"$PYTHON_EXE" -m installer.verify_environment || echo "[WARN] Environment check had warnings."

# 3. Start Backend Server
echo "[*] Starting local backend service on http://127.0.0.1:8765 ..."
"$PYTHON_EXE" -m apps.processing.server &
SERVER_PID=$!

# Trap exit to cleanup background server
trap "kill $SERVER_PID 2>/dev/null || true" EXIT

sleep 2

# 4. Launch Desktop UI
if [ -f "apps/desktop/src-tauri/target/release/cil-report-desktop" ]; then
    echo "[*] Launching Native Tauri Desktop Application..."
    apps/desktop/src-tauri/target/release/cil-report-desktop
elif [ -f "apps/desktop/dist/index.html" ]; then
    echo "[*] Opening embedded static desktop interface in default browser..."
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://127.0.0.1:8765/
    elif command -v open >/dev/null 2>&1; then
        open http://127.0.0.1:8765/
    fi
    wait $SERVER_PID
elif command -v npm >/dev/null 2>&1; then
    echo "[*] Launching Vite Development Server..."
    (cd apps/desktop && npm run dev)
else
    echo "[*] Opening browser to local service..."
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://127.0.0.1:8765/
    elif command -v open >/dev/null 2>&1; then
        open http://127.0.0.1:8765/
    fi
    wait $SERVER_PID
fi
