@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "APP_DIR=%CD%\ggf-lens-turbo"
if exist "%CD%\helpers\lens_turbo_u4_ui.py" set "APP_DIR=%CD%"

:: Check for Conda environment first
set "CONDA_ENV=%APP_DIR%\environments\conda"
set "VENV_PY=%CONDA_ENV%\python.exe"

if not exist "%VENV_PY%" (
    :: Fallback to traditional venv
    set "VENV_PY=%APP_DIR%\venv\Scripts\python.exe"
)

if not exist "%VENV_PY%" (
    set "VENV_PY=%APP_DIR%\environments\.lens_turbo_u4\Scripts\python.exe"
)

if not exist "%APP_DIR%\helpers\lens_turbo_u4_ui.py" (
    echo [ERROR] App files not found. Run install.bat first.
    pause
    exit /b 1
)

if not exist "%VENV_PY%" (
    echo [ERROR] Python environment not found. Run install.bat first.
    pause
    exit /b 1
)

set "HF_HOME=%APP_DIR%\models\lens\hf_home"
set "HF_HUB_CACHE=%APP_DIR%\models\lens\hf_cache"
set "HUGGINGFACE_HUB_CACHE=%HF_HUB_CACHE%"
set "TRANSFORMERS_CACHE=%APP_DIR%\models\lens\transformers_cache"
set "TRITON_CACHE_DIR=%APP_DIR%\models\lens\triton_cache"
set "KERNELS_CACHE=%APP_DIR%\models\lens\kernels_cache"
set "TORCH_HOME=%APP_DIR%\models\lens\torch_home"
set "PYTHONPATH=%APP_DIR%\models\lens\repos\Lens"

echo.
echo Starting Get Going Fast ^| Lens Turbo UI...
echo Fast mode keeps the loaded model on your GPU. Enable CPU offload only when VRAM is insufficient.
echo.

"%VENV_PY%" "%APP_DIR%\helpers\lens_turbo_u4_ui.py"
if errorlevel 1 (
    echo [ERROR] Lens Turbo exited with an error.
    pause
    exit /b 1
)

pause
exit /b 0
