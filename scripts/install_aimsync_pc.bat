@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

echo AimSync PC - first-time setup
echo.

call "%~dp0_ensure_venv.bat"
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo NDI check:
.venv\Scripts\python.exe scripts\diagnose_ndi.py
echo.
echo Done. Use scripts\run.bat for production ^(Makcu^).
pause
