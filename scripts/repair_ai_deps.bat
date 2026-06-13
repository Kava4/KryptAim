@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
call "%~dp0_ensure_venv.bat"
if errorlevel 1 pause & exit /b 1
echo.
echo Done. Restart run.bat
pause
