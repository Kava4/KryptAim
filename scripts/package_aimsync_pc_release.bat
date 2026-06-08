@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

set "OUT=release\AimSync-PC"
set "STAGE=%OUT%-stage"

echo Packaging AimSync PC release (venv deploy, no bundled exe)...
echo.

if exist "%STAGE%" rmdir /s /q "%STAGE%"
if exist "%OUT%" rmdir /s /q "%OUT%" 2>nul
mkdir "%STAGE%" 2>nul

REM Core app
for %%D in (AI Config Makcu Recoil Server PatternGenerator packaging scripts) do (
    if exist "%%D" (
        echo   + %%D\
        xcopy /E /I /Q /Y "%%D" "%STAGE%\%%D\" >nul
    )
)

for %%F in (main.py requirements.txt requirements-aimsync-pc.txt) do (
    if exist "%%F" copy /Y "%%F" "%STAGE%\" >nul
)

REM User-facing readme in package root
if exist "release\README-AimSync-PC.txt" (
    copy /Y "release\README-AimSync-PC.txt" "%STAGE%\README.txt" >nul
)

REM Remove junk from stage
for %%D in (aimsync-venv build-venv build dist release .git .cursor __pycache__ vendor-ai-reference) do (
    if exist "%STAGE%\%%D" rmdir /s /q "%STAGE%\%%D" 2>nul
)

if exist "%OUT%.zip" del /f "%OUT%.zip"
if exist "%OUT%" rmdir /s /q "%OUT%" 2>nul
move "%STAGE%" "%OUT%" >nul

powershell -NoProfile -Command "Compress-Archive -Path '%OUT%\*' -DestinationPath '%OUT%.zip' -Force"
if errorlevel 1 (
    echo [WARN] Could not create zip — folder ready: %OUT%\
    goto :done
)

echo.
echo Created:
echo   Folder: %OUT%\
echo   Zip:    %OUT%.zip
echo.
echo Package ready: release\AimSync-PC.zip
echo User runs: scripts\install_aimsync_pc.bat then scripts\run_aimsync.bat

:done
pause
