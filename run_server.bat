@echo off
setlocal enabledelayedexpansion
title CIL Local AI Processing Server

echo ======================================================================
echo   CIL Local AI Report Generator -- Processing Service
echo ======================================================================

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
    echo [ERROR] Python 3.11+ was not found.
    pause
    exit /b 1
)

echo Starting server on 127.0.0.1:8765 (Air-gapped / Local Loopback only)...
"%PYTHON_EXE%" -m apps.processing.server
