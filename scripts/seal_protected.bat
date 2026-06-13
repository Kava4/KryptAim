@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

call "%~dp0_ensure_venv.bat"
if errorlevel 1 exit /b 1

echo Sealing protected modules from app\_src\ ...
.venv\Scripts\python.exe scripts\seal_protected.py
exit /b %ERRORLEVEL%
