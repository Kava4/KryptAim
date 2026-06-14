@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

if not exist "build-venv\Scripts\python.exe" (
    echo [ERROR] build-venv missing. Run scripts\create_build_venv.bat first.
    pause
    exit /b 1
)

set KRYPTAIM_BUILD_PROFILE=full
echo [build] FULL profile — bundles torch/ultralytics ^(~2-4 GB^)
echo.
build-venv\Scripts\python.exe build_app.py
if errorlevel 1 pause & exit /b 1
echo.
echo Done: dist\KryptAim\KryptAim.exe
pause
