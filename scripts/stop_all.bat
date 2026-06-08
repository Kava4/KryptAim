@echo off
setlocal
title AimSync - Stop All

echo [AimSync] Stopping running processes...

taskkill /F /IM AimSync.exe >nul 2>&1
taskkill /F /IM AimSync.exe >nul 2>&1
taskkill /F /IM AimSyncBeta.exe >nul 2>&1

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
)

echo [AimSync] Done.
echo.
if /I not "%~1"=="--silent" pause
