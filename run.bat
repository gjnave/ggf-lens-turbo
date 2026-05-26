@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

cd /d "%~dp0"
set "SCRIPT_DIR=%~dp0"
set "VENV_PY=%SCRIPT_DIR%venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [ERROR] venv not found. Run install.bat first.
    pause & exit /b 1
)

if not exist "%SCRIPT_DIR%helpers\lens_turbo_u4_ui.py" (
    echo [ERROR] helpers\lens_turbo_u4_ui.py not found.
    echo         Make sure you extracted the full lens_turbo.zip contents here:
    echo         %SCRIPT_DIR%
    pause & exit /b 1
)

:: Portable model/cache dirs -- keeps everything on this drive
set "HF_HOME=%SCRIPT_DIR%models\lens\hf_home"
set "HF_HUB_CACHE=%SCRIPT_DIR%models\lens\hf_cache"
set "HUGGINGFACE_HUB_CACHE=%SCRIPT_DIR%models\lens\hf_cache"
set "TRANSFORMERS_CACHE=%SCRIPT_DIR%models\lens\transformers_cache"
set "TRITON_CACHE_DIR=%SCRIPT_DIR%models\lens\triton_cache"
set "KERNELS_CACHE=%SCRIPT_DIR%models\lens\kernels_cache"
set "TORCH_HOME=%SCRIPT_DIR%models\lens\torch_home"
set "PYTHONPATH=%SCRIPT_DIR%models\lens\repos\Lens"

echo.
echo Starting Get Going Fast ^| Lens Turbo UI...
echo First run will download model files -- this will take a while.
echo Fast mode keeps the loaded model on your GPU. Enable CPU offload only when VRAM is insufficient.
echo.

"%VENV_PY%" "%SCRIPT_DIR%helpers\lens_turbo_u4_ui.py"
if errorlevel 1 ( echo [ERROR] Lens Turbo exited with an error. & pause & exit /b 1 )

pause
exit /b 0
