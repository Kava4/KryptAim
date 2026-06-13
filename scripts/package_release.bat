@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

if exist "dist\AimSync.exe" goto :onefile
if exist "dist\AimSync\AimSync.exe" goto :onedir
echo [ERROR] No build found - run scripts\build_app.bat first.
exit /b 1

:onefile
if exist "dist\AimSync.zip" del /f "dist\AimSync.zip"
powershell -NoProfile -Command "Compress-Archive -LiteralPath 'dist\AimSync.exe' -DestinationPath 'dist\AimSync.zip' -Force"
if errorlevel 1 (
    echo [WARN] zip failed - exe ready: dist\AimSync.exe
    exit /b 1
)
echo Created: dist\AimSync.zip  (contains AimSync.exe only)
exit /b 0

:onedir
if exist "dist\AimSync.zip" del /f "dist\AimSync.zip"
powershell -NoProfile -Command "Compress-Archive -LiteralPath 'dist\AimSync' -DestinationPath 'dist\AimSync.zip' -Force"
if errorlevel 1 (
    echo [WARN] zip failed - folder ready: dist\AimSync\
    exit /b 1
)
echo Created: dist\AimSync.zip  (full onedir bundle)
exit /b 0
