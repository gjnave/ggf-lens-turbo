@echo off
setlocal
cd /d "%~dp0"

set "REPO_URL=https://github.com/gjnave/ggf-lens-turbo.git"
set "APP_DIR=%CD%\ggf-lens-turbo"
if exist "%CD%\requirements.txt" set "APP_DIR=%CD%"

if exist "disclaimer.md" (
    type "disclaimer.md"
    echo.
)
if exist "about.nfo" (
    type "about.nfo"
    echo.
)

echo Get Going Fast ^| Lens Turbo
echo Simple local setup
echo.

if not exist "%APP_DIR%" (
    echo Cloning app files from GitHub...
    git clone --depth 1 "%REPO_URL%" "%APP_DIR%" || goto :error
) else if /I not "%APP_DIR%"=="%CD%" (
    echo Updating app files from GitHub...
    git -C "%APP_DIR%" pull --ff-only || goto :error
)

pushd "%APP_DIR%" || goto :error

if not exist "venv\Scripts\python.exe" (
    echo Creating Python 3.11 virtual environment...
    py -3.11 -m venv venv || goto :error
)

set "PY=%APP_DIR%\venv\Scripts\python.exe"
set "HF_HOME=%APP_DIR%\models\lens\hf_home"
set "HF_HUB_CACHE=%APP_DIR%\models\lens\hf_cache"
set "HUGGINGFACE_HUB_CACHE=%HF_HUB_CACHE%"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "TRANSFORMERS_CACHE=%APP_DIR%\models\lens\transformers_cache"
set "HF_MODULES_CACHE=%APP_DIR%\models\lens\hf_modules"
set "TRITON_CACHE_DIR=%APP_DIR%\models\lens\triton_cache"
set "KERNELS_CACHE=%APP_DIR%\models\lens\kernels_cache"
set "TORCH_HOME=%APP_DIR%\models\lens\torch_home"

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

popd
echo.
echo Done. Run run.bat.
pause
exit /b 0

:error
popd 2>nul
echo.
echo Install failed. See the error above.
pause
exit /b 1
