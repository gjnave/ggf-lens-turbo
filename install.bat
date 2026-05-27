@echo off
setlocal
cd /d "%~dp0"

echo.
echo Get Going Fast ^| Lens Turbo
echo Simple local setup
echo.

if not exist "venv\Scripts\python.exe" (
    echo Creating Python 3.11 virtual environment...
    py -3.11 -m venv venv || goto :error
)

set "PY=%CD%\venv\Scripts\python.exe"
set "HF_HOME=%CD%\models\lens\hf_home"
set "HF_HUB_CACHE=%CD%\models\lens\hf_cache"
set "HUGGINGFACE_HUB_CACHE=%HF_HUB_CACHE%"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "TRANSFORMERS_CACHE=%CD%\models\lens\transformers_cache"
set "HF_MODULES_CACHE=%CD%\models\lens\hf_modules"
set "TRITON_CACHE_DIR=%CD%\models\lens\triton_cache"
set "KERNELS_CACHE=%CD%\models\lens\kernels_cache"
set "TORCH_HOME=%CD%\models\lens\torch_home"

echo Installing Python packages...
"%PY%" -m pip install --upgrade pip wheel || goto :error
"%PY%" -m pip install "setuptools==70.2.0" || goto :error
"%PY%" -m pip install "torch>=2.8.0,<2.12" torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128 || goto :error
"%PY%" -m pip install -r requirements.txt || goto :error
"%PY%" -m pip install "setuptools==70.2.0" || goto :error
"%PY%" -m pip check || goto :error

if not exist "models\lens\repos\Lens\lens" (
    echo Cloning Microsoft Lens...
    git clone --depth 1 https://github.com/microsoft/Lens.git "models\lens\repos\Lens" || goto :error
) else (
    echo Microsoft Lens is already present.
)

echo Downloading Lens Turbo model...
"%PY%" -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='WaveCut/Lens-Turbo-SDNQ-uint4-static', cache_dir=r'%HF_HUB_CACHE%')" || goto :error

echo Preparing quantized GPU kernels...
"%PY%" -c "from kernels import get_kernel; get_kernel('kernels-community/gpt-oss-triton-kernels', version=1, trust_remote_code=True)" || goto :error

echo.
echo Done. Run run.bat.
pause
exit /b 0

:error
echo.
echo Install failed. See the error above.
pause
exit /b 1
