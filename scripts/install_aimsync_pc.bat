@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

set "VENV=aimsync-venv"
set "PY_MIN=3.10"

echo ============================================================
echo  AimSync - install on this PC (venv, no bundled exe)
echo ============================================================
echo.
echo Use this on the AimSync PC (GPU + Makcu + NDI).
echo Copy the whole AimSync folder here, then run this script once.
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Install Python %PY_MIN%+ from https://www.python.org/downloads/
    echo Check "Add python.exe to PATH" during setup.
    pause
    exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo [ERROR] Python 3.10 or newer is required.
    python --version
    pause
    exit /b 1
)

if not exist "%VENV%\Scripts\python.exe" (
    echo Creating virtual environment: %VENV%
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
) else (
    echo Using existing venv: %VENV%
)

set "PY=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\python.exe -m pip"

echo.
echo Upgrading pip...
"%PY%" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo.
echo Stopping AimSync if running (unlocks onnxruntime DLLs for pip)...
call "%~dp0stop_all.bat" --silent >nul 2>&1

echo.
echo Installing AimSync dependencies...
"%PY%" -m pip install -r requirements-aimsync-pc.txt
if errorlevel 1 exit /b 1

echo.
echo Installing onnx + onnxruntime-gpu (Ultralytics .onnx on CUDA)...
"%PY%" -m pip install --upgrade onnx onnxruntime-gpu
if errorlevel 1 exit /b 1

echo.
echo Installing PyTorch CUDA 12.6 (replace any CPU-only torch)...
"%PY%" -m pip uninstall -y torch torchvision torchaudio 2>nul
"%PY%" -m pip install --force-reinstall --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
if errorlevel 1 exit /b 1
"%PY%" -c "import torch; assert '+cu' in torch.__version__ and torch.cuda.is_available(), torch.__version__"
if errorlevel 1 (
    echo [ERROR] torch is still CPU or cuda=False — run scripts\repair_ai_deps.bat after installing NVIDIA driver
    pause
    exit /b 1
)

echo.
echo Verifying AI + Makcu stack...
"%PY%" scripts\verify_build_ai_stack.py
if errorlevel 1 (
    echo [ERROR] Verification failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Install OK
echo ============================================================
echo.
echo Also install on BOTH PCs:
echo   NDI Runtime  https://ndi.link/NDIRedistV6
echo.
echo On this AimSync PC (NVIDIA GPU):
echo   CUDA 12.6    https://developer.nvidia.com/cuda-12-6-0-download-archive
echo.
echo Put models in: %%APPDATA%%\AimSync\bin\models\
echo   e.g. cs2_640.onnx
echo.
echo Start AimSync:
echo   scripts\run_aimsync.bat
echo.
pause
