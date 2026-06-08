@echo off
cd /d "%~dp0.."
if not exist "build-venv\Scripts\python.exe" (
    echo [ERROR] build-venv missing. Run scripts\create_build_venv.bat first.
    pause
    exit /b 1
)
build-venv\Scripts\python.exe build_app.py
if errorlevel 1 pause
