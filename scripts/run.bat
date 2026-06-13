@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

call "%~dp0_ensure_venv.bat"
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo [prod] Makcu required - opens browser at http://localhost:5000
echo.

.venv\Scripts\python.exe main.py
set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" echo Exit code: %EC%
pause
exit /b %EC%
