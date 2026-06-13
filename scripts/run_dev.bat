@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

call "%~dp0_ensure_venv.bat"
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo [dev] AIMSYNC_DEV=1 - web UI, local mouse if no Makcu, dev license keys
echo [dev] AI unlock key: DEV-AIMSYNC  (Global Settings -^> Validate)
echo.

set AIMSYNC_DEV=1
.venv\Scripts\python.exe main.py --dev
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" echo Exit code: %EC%
pause
exit /b %EC%
