@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

if not exist "build-venv\Scripts\python.exe" (
    echo [ERROR] build-venv missing. Run scripts\create_build_venv.bat first.
    pause
    exit /b 1
)

echo [release] Clean rebuild + zip
set KRYPTAIM_BUILD_CLEAN=1
build-venv\Scripts\python.exe build_app.py
if errorlevel 1 (
    pause
    exit /b 1
)

call "%~dp0package_release.bat"
pause
