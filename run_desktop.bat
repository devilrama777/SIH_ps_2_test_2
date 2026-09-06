@echo off
setlocal enabledelayedexpansion
title CIL Local AI Report Generator

echo ======================================================================
echo   CIL Local AI Report Generator -- Starting Platform (Local-First)
echo ======================================================================

:: 1. Locate Python executable
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=python"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python 3.11+ was not found in .venv\Scripts\ or system PATH.
    echo Please install Python 3.11+ or initialize virtual environment.
    pause
    exit /b 1
)

:: 2. Pre-flight Environment Check
echo [*] Running pre-flight environment diagnostics...
"%PYTHON_EXE%" -m installer.verify_environment
if !errorlevel! neq 0 (
    echo [WARNING] Some environment checks reported warnings or errors.
)

:: 3. Launch Python Local Processing Server
echo [*] Launching CIL Processing Service on http://127.0.0.1:8000 ...
start "CIL Backend Service" /min "%PYTHON_EXE%" -m apps.processing.server

:: Wait 3 seconds for server to bind port
timeout /t 3 /nobreak >nul

:: 4. Launch Desktop Interface
echo [*] Launching Desktop User Interface...
if exist "apps\desktop\src-tauri\target\release\cil-report-desktop.exe" (
    echo Launching Native Tauri Desktop Application...
    start "" "apps\desktop\src-tauri\target\release\cil-report-desktop.exe"
) else (
    where npm >nul 2>&1
    if !errorlevel! equ 0 (
        echo Launching Desktop in Dev/Vite Mode...
        cd apps\desktop
        start "CIL Desktop UI" npm.cmd run dev
        cd ..\..
    ) else (
        echo [INFO] Opening default browser to local backend...
        start http://127.0.0.1:8000/docs
    )
)

echo ======================================================================
echo   Platform running successfully!
echo   - Backend: http://127.0.0.1:8000 (Local Loopback)
echo   - Health Check: http://127.0.0.1:8000/api/v1/health
echo ======================================================================
