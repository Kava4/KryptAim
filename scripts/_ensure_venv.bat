@echo off
REM Ensure .venv works on THIS PC + AI deps present.
setlocal EnableExtensions

set "ROOT=%~dp0.."
cd /d "%ROOT%"

set "VENV_PY=.venv\Scripts\python.exe"
set "NEED_CREATE=0"
set "NEED_INSTALL=0"

if not exist "%VENV_PY%" (
    set "NEED_CREATE=1"
) else (
    "%VENV_PY%" -c "import sys" >nul 2>&1
    if errorlevel 1 set "NEED_CREATE=1"
)

if "%NEED_CREATE%"=="1" goto :create_venv

REM Venv OK — still verify packages (venv may predate requirements.txt changes).
"%VENV_PY%" -c "import flask" >nul 2>&1
if errorlevel 1 set "NEED_INSTALL=1"
"%VENV_PY%" -c "import ultralytics, cyndilib, cv2, numpy, onnxruntime" >nul 2>&1
if errorlevel 1 set "NEED_INSTALL=1"
if "%NEED_INSTALL%"=="1" goto :install_deps
exit /b 0

:create_venv
if exist ".venv" (
    echo.
    echo [venv] Removing broken .venv ^(wrong PC or missing Python^)...
    rmdir /s /q ".venv" 2>nul
)

set "CREATED=0"
py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    echo [venv] Creating with: py -3.12
    py -3.12 -m venv ".venv"
    if not errorlevel 1 set "CREATED=1"
)
if "%CREATED%"=="0" (
    py -3 -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        echo [venv] Creating with: py -3
        py -3 -m venv ".venv"
        if not errorlevel 1 set "CREATED=1"
    )
)
if "%CREATED%"=="0" (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        echo [venv] Creating with: python
        python -m venv ".venv"
        if not errorlevel 1 set "CREATED=1"
    )
)
if "%CREATED%"=="0" (
    echo ERROR: No working Python found. Install Python 3.12+ with Add to PATH.
    exit /b 1
)
if not exist "%VENV_PY%" (
    echo ERROR: venv creation failed.
    exit /b 1
)
set "NEED_INSTALL=1"

:install_deps
echo [venv] Installing / updating dependencies...
"%VENV_PY%" -m pip install -U pip -q
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed.
    exit /b 1
)
echo.
echo [venv] Checking AI stack...
"%VENV_PY%" -c "import ultralytics; print('  ultralytics OK')"
if errorlevel 1 (
    echo ERROR: ultralytics still missing after install.
    exit /b 1
)
"%VENV_PY%" -c "import flask; print('  Flask OK')"
if errorlevel 1 (
    echo ERROR: Flask still missing after install.
    exit /b 1
)
"%VENV_PY%" -c "import torch; print('  torch', torch.__version__, 'cuda=', torch.cuda.is_available())" 2>nul
if errorlevel 1 (
    echo   torch not installed ^(optional for CPU test^)
    echo   GPU: .venv\Scripts\pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
)
echo [venv] Ready.
exit /b 0
