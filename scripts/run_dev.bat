@echo off
setlocal
cd /d "%~dp0.."

call "%~dp0stop_all.bat" --silent >nul 2>&1

if exist "aimsync-venv\Scripts\python.exe" (
    set "PY=aimsync-venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PY=venv\Scripts\python.exe"
) else (
    set "PY=python"
)

echo [AimSync] Starting (%PY%)...
"%PY%" main.py
