@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
set "PY=aimsync-venv\Scripts\python.exe"
set "CU_INDEX=https://download.pytorch.org/whl/cu126"

if not exist "%PY%" (
    echo Run scripts\install_aimsync_pc.bat first.
    pause
    exit /b 1
)

echo ============================================================
echo  Repair AI deps (CUDA torch + onnxruntime-gpu)
echo ============================================================
echo Close AimSync completely, then press a key...
pause >nul

call "%~dp0stop_all.bat" --silent >nul 2>&1

echo.
echo [1/3] Remove CPU torch / conflicting onnxruntime...
"%PY%" -m pip uninstall -y torch torchvision torchaudio onnxruntime onnxruntime-directml 2>nul

echo.
echo [2/3] Install onnxruntime-gpu + onnx...
"%PY%" -m pip install --upgrade onnx onnxruntime-gpu
if errorlevel 1 exit /b 1

echo.
echo [3/3] Install PyTorch CUDA 12.6 (force, no CPU wheel)...
"%PY%" -m pip install --force-reinstall --no-cache-dir torch torchvision torchaudio --index-url %CU_INDEX%
if errorlevel 1 (
    echo [ERROR] cu126 install failed. Check NVIDIA driver and internet.
    pause
    exit /b 1
)

echo.
"%PY%" -c "import torch; v=torch.__version__; c=torch.cuda.is_available(); print('torch', v, 'cuda=', c); raise SystemExit(0 if c and '+cu' in v else 1)"
if errorlevel 1 (
    echo.
    echo [ERROR] Still CPU torch or cuda=False. Try:
    echo   nvidia-smi
    echo   Install CUDA 12.6 driver/runtime from NVIDIA
    pause
    exit /b 1
)

echo.
"%PY%" scripts\verify_build_ai_stack.py
pause
