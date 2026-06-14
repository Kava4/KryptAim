@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

if not defined KRYPTAIM_WEAPON_ICONS (
    set "KRYPTAIM_WEAPON_ICONS=e:\projects\cs2-webradar-usermode\release\dist\assets\icons"
)

echo Sync weapon icons from:
echo   %KRYPTAIM_WEAPON_ICONS%
echo.

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe scripts\sync_weapon_icons.py
) else if exist "build-venv\Scripts\python.exe" (
    build-venv\Scripts\python.exe scripts\sync_weapon_icons.py
) else (
    python scripts\sync_weapon_icons.py
)

set "EC=%ERRORLEVEL%"
if not "%EC%"=="0" pause
exit /b %EC%
