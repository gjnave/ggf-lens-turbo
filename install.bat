@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

cd /d "%~dp0"
set "SCRIPT_DIR=%~dp0"

IF EXIST "disclaimer.md" ( TYPE "disclaimer.md" & pause )
IF EXIST "about.nfo" TYPE "about.nfo"

echo.
echo ================================================================
echo  Lens Turbo SDNQ UINT4 -- Installer
echo ================================================================
echo.

:: Find Python
set "BASE_PYTHON="
for /f "usebackq delims=" %%P in (`py -3 -c "import sys; print(sys.executable)" 2^>nul`) do set "BASE_PYTHON=%%P"
if not defined BASE_PYTHON for /f "usebackq delims=" %%P in (`where python 2^>nul`) do if not defined BASE_PYTHON set "BASE_PYTHON=%%P"
if not defined BASE_PYTHON (
    echo [ERROR] Python 3 not found. Install Python 3.10+ and rerun.
    pause & exit /b 1
)
echo [OK] Python: %BASE_PYTHON%

:: Create venv
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    "%BASE_PYTHON%" -m venv venv
    if errorlevel 1 ( echo [ERROR] venv creation failed. & pause & exit /b 1 )
)

call venv\Scripts\activate

:: Redirect pip cache and temp to this drive -- prevents "no space" errors when C: is the default
set "PIP_CACHE_DIR=%SCRIPT_DIR%pip_cache"
set "TEMP=%SCRIPT_DIR%tmp"
set "TMP=%SCRIPT_DIR%tmp"
if not exist "%SCRIPT_DIR%tmp" mkdir "%SCRIPT_DIR%tmp"

python -m pip install --upgrade pip wheel setuptools

:: PyTorch
where nvidia-smi >nul 2>nul
if not errorlevel 1 (
    echo NVIDIA GPU detected -- installing CUDA PyTorch...
    pip install "torch>=2.8.0" torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
) else (
    echo [WARN] NVIDIA GPU not detected. Lens Turbo requires CUDA. Installing CPU torch for setup only.
    pip install torch torchvision torchaudio
)
if errorlevel 1 ( echo [ERROR] PyTorch install failed. & pause & exit /b 1 )

:: Core deps
pip install "diffusers>=0.35.1" "transformers>=4.57.1" accelerate safetensors huggingface_hub sentencepiece protobuf pillow numpy scipy einops peft tqdm PySide6
if errorlevel 1 ( echo [ERROR] Dependency install failed. & pause & exit /b 1 )

:: Quant / SDNQ stack
pip install "triton-windows<3.7" kernels bitsandbytes sdnq
if errorlevel 1 ( echo [ERROR] SDNQ/Triton install failed. & pause & exit /b 1 )

:: Microsoft Lens repo ^(needed for LensPipeline^)
if not exist "models\lens\repos\Lens\lens" (
    echo Cloning Microsoft Lens repo...
    git clone --depth 1 https://github.com/microsoft/Lens "models\lens\repos\Lens"
    if errorlevel 1 ( echo [ERROR] Git clone failed. & pause & exit /b 1 )
) else (
    echo Existing Lens repo found. Pulling latest...
    cd /d "%SCRIPT_DIR%models\lens\repos\Lens"
    git pull
    cd /d "%SCRIPT_DIR%"
)

if errorlevel 1 ( echo [ERROR] Lens package install failed. & pause & exit /b 1 )

echo.
echo [OK] Install complete.
echo      Run run.bat to launch the UI.
echo      Run run_lens_test.bat to run a quick generation test.
echo.
pause
exit /b 0
