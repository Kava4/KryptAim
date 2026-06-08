@echo off
setlocal
cd /d "%~dp0.."

set "VENV=aimsync-venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
    echo AimSync venv not found. Run once:
    echo   scripts\install_aimsync_pc.bat
    pause
    exit /b 1
)

set "YOLO_AUTOINSTALL=false"
echo Starting AimSync...
"%PY%" main.py
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
    echo AimSync exited with code %EXITCODE%
    pause
)
exit /b %EXITCODE%
