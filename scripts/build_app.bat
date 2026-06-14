@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

if not exist "build-venv\Scripts\python.exe" (
    echo [ERROR] build-venv missing. Run scripts\create_build_venv.bat first.
    pause
    exit /b 1
)

echo [build] LITE profile (default) — slim exe, AI installs to AppData on first use
echo       Full offline bundle: scripts\build_app_full.bat
echo.
set KRYPTAIM_BUILD_PROFILE=lite
build-venv\Scripts\python.exe build_app.py
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo Done: dist\KryptAim.exe  (single file, no _internal)
echo Zip:   scripts\package_release.bat
pause
