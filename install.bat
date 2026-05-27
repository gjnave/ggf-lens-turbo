@echo off
setlocal
cd /d "%~dp0"

set "REPO_URL=https://github.com/gjnave/ggf-lens-turbo.git"
set "APP_DIR=%CD%\ggf-lens-turbo"
set "ARIA2=%CD%\aria2c.exe"
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
set "TMP_DIR=%APP_DIR%\tmp"
if not exist "%TMP_DIR%" mkdir "%TMP_DIR%"

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

call :download_hf_repo "WaveCut/Lens-Turbo-SDNQ-uint4-static" "%HF_HUB_CACHE%\models--WaveCut--Lens-Turbo-SDNQ-uint4-static" "model" || goto :error
call :download_hf_repo "kernels-community/gpt-oss-triton-kernels" "%KERNELS_CACHE%\kernels--kernels-community--gpt-oss-triton-kernels" "kernel" || goto :error

popd
echo.
echo Done. Run run.bat.
pause
exit /b 0

:download_hf_repo
set "HF_REPO=%~1"
set "HF_DEST=%~2"
set "HF_KIND=%~3"
set "HF_META_JSON=%TMP_DIR%\%HF_KIND%-meta.json"
set "HF_URLS_TXT=%TMP_DIR%\%HF_KIND%-urls.txt"
set "HF_REF_FILE=%HF_DEST%\refs\main"
set "HF_MANIFEST_SCRIPT=%APP_DIR%\helpers\build_hf_manifest.ps1"

if exist "%HF_REF_FILE%" (
    echo %HF_KIND% cache already present for %HF_REPO%.
    exit /b 0
)

echo Downloading %HF_KIND% file list for %HF_REPO%...
curl.exe -L --fail --output "%HF_META_JSON%" "https://huggingface.co/api/models/%HF_REPO%" >nul || exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -File "%HF_MANIFEST_SCRIPT%" -Repo "%HF_REPO%" -Dest "%HF_DEST%" -MetaJson "%HF_META_JSON%" -UrlsTxt "%HF_URLS_TXT%" || exit /b 1

echo Downloading %HF_KIND% files for %HF_REPO%...
if exist "%ARIA2%" (
    "%ARIA2%" --continue=true --auto-file-renaming=false --allow-overwrite=true --max-connection-per-server=8 --split=8 --input-file="%HF_URLS_TXT%" || exit /b 1
) else (
    echo aria2c.exe not found. Falling back to curl...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$lines=Get-Content -LiteralPath '%HF_URLS_TXT%'; for($i=0; $i -lt $lines.Count; $i+=3){ $url=$lines[$i]; $dir=$lines[$i+1].Substring(6); $name=$lines[$i+2].Substring(6); $out=Join-Path $dir $name; curl.exe -L --fail --output $out $url; if($LASTEXITCODE -ne 0){ exit $LASTEXITCODE } }" || exit /b 1
)
exit /b 0

:fetch_file
set "FETCH_URL=%~1"
set "FETCH_OUT=%~2"
if exist "%ARIA2%" (
    "%ARIA2%" --continue=true --auto-file-renaming=false --allow-overwrite=true --dir="%~dp2" --out="%~nx2" "%FETCH_URL%" >nul || exit /b 1
) else (
    curl.exe -L --fail --output "%FETCH_OUT%" "%FETCH_URL%" >nul || exit /b 1
)
exit /b 0

:error
popd 2>nul
echo.
echo Install failed. See the error above.
pause
exit /b 1
