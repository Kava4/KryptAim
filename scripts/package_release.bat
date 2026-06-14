@echo off

setlocal EnableExtensions

cd /d "%~dp0.."



if exist "dist\KryptAim.exe" goto :onefile

if exist "dist\KryptAim\KryptAim.exe" goto :onedir

echo [ERROR] No build found - run scripts\build_app.bat first.

exit /b 1



:onefile

if exist "dist\KryptAim.zip" del /f "dist\KryptAim.zip"

powershell -NoProfile -Command "Compress-Archive -LiteralPath 'dist\KryptAim.exe' -DestinationPath 'dist\KryptAim.zip' -Force"

if errorlevel 1 (

    echo [WARN] zip failed - exe ready: dist\KryptAim.exe

    exit /b 1

)

echo Created: dist\KryptAim.zip  (contains KryptAim.exe only)

exit /b 0



:onedir

if exist "dist\KryptAim.zip" del /f "dist\KryptAim.zip"

powershell -NoProfile -Command "Compress-Archive -LiteralPath 'dist\KryptAim' -DestinationPath 'dist\KryptAim.zip' -Force"

if errorlevel 1 (

    echo [WARN] zip failed - folder ready: dist\KryptAim\

    exit /b 1

)

echo Created: dist\KryptAim.zip  (full onedir bundle)

exit /b 0

