@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
set "VENV=build-venv"

if exist "%VENV%\Scripts\python.exe" (
    echo Build venv exists: %VENV%
    "%VENV%\Scripts\python.exe" -c "import sys; print('Python', sys.version)"
    goto :install
)

set "PYBOOT="
for %%V in (3.12 3.11 3.10) do (
    if not defined PYBOOT (
        py -%%V -c "import sys" >nul 2>&1 && set "PYBOOT=py -%%V"
    )
)

if not defined PYBOOT (
    echo [ERROR] Need Python 3.10-3.12. Install from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Creating build venv: %PYBOOT%
%PYBOOT% -m venv "%VENV%"
if errorlevel 1 exit /b 1

:install
call "%VENV%\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
echo.
echo Installing CUDA PyTorch 12.6...
python -m pip uninstall -y torch torchvision torchaudio 2>nul
python -m pip install --force-reinstall --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
if errorlevel 1 (
    echo [ERROR] CUDA torch install failed
    pause
    exit /b 1
)
echo.
"%VENV%\Scripts\python.exe" scripts\verify_build_stack.py
if errorlevel 1 pause & exit /b 1
echo.
echo Ready. Run: scripts\build_app.bat
pause
