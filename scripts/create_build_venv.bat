@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
set "VENV=build-venv"

if exist "%VENV%\Scripts\python.exe" (
    echo Build venv already exists: %VENV%
    "%VENV%\Scripts\python.exe" -c "import sys; print('Python', sys.version)"
    goto :install
)

REM Prefer 3.12 / 3.11 / 3.10 — avoid 3.13+ for PyInstaller + torch bundles
set "PYBOOT="
for %%V in (3.12 3.11 3.10) do (
    if not defined PYBOOT (
        py -%%V -c "import sys" >nul 2>&1 && set "PYBOOT=py -%%V"
    )
)

if not defined PYBOOT (
    echo.
    echo [ERROR] No Python 3.10-3.12 found. Install Python 3.12 from https://www.python.org/downloads/
    echo         PyInstaller + torch frozen builds are unreliable on 3.13+.
    echo.
    pause
    exit /b 1
)

echo Creating CUDA build venv with: %PYBOOT%
%PYBOOT% -m venv "%VENV%"
if errorlevel 1 exit /b 1

:install
call "%VENV%\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install pyinstaller pillow
pip install -r requirements-aimsync-pc.txt
echo.
echo Installing onnx + onnxruntime-gpu...
python -m pip install --upgrade onnx onnxruntime-gpu
if errorlevel 1 exit /b 1
echo.
echo Installing PyTorch CUDA 12.6 (replace CPU torch from ultralytics)...
python -m pip uninstall -y torch torchvision torchaudio 2>nul
python -m pip install --force-reinstall --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
if errorlevel 1 exit /b 1
python -c "import torch; assert '+cu' in torch.__version__ and torch.cuda.is_available(), torch.__version__"
if errorlevel 1 (
    echo [ERROR] torch is still CPU or cuda=False — check nvidia-smi and NVIDIA driver
    pause
    exit /b 1
)
echo Verifying AI stack...
"%VENV%\Scripts\python.exe" scripts\verify_build_ai_stack.py
if errorlevel 1 exit /b 1
echo.
echo Build venv ready. Run:
echo   scripts\build_app.bat
echo.
echo AimSync PC also needs NVIDIA CUDA 12.6 runtime:
echo   https://developer.nvidia.com/cuda-12-6-0-download-archive
pause
