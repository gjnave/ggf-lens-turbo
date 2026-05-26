@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

cd /d "%~dp0"
set "SCRIPT_DIR=%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] venv not found. Run install.bat first.
    pause & exit /b 1
)

call venv\Scripts\activate

set "HF_HOME=%SCRIPT_DIR%models\lens\hf_home"
set "HF_HUB_CACHE=%SCRIPT_DIR%models\lens\hf_cache"
set "HUGGINGFACE_HUB_CACHE=%SCRIPT_DIR%models\lens\hf_cache"
set "TRANSFORMERS_CACHE=%SCRIPT_DIR%models\lens\transformers_cache"
set "TRITON_CACHE_DIR=%SCRIPT_DIR%models\lens\triton_cache"
set "KERNELS_CACHE=%SCRIPT_DIR%models\lens\kernels_cache"
set "TORCH_HOME=%SCRIPT_DIR%models\lens\torch_home"

echo.
set "PYTHONPATH=%SCRIPT_DIR%models\lens\repos\Lens"
echo Running Get Going Fast ^| Lens Turbo generation test...
echo Fast/default: run_lens_test.bat --prompt "a neon robot" --steps 4 --cfg 1
echo Low VRAM/slower: add --offload
echo.

python "%SCRIPT_DIR%helpers\lens_turbo_u4_test.py" %*
set "ERR=%ERRORLEVEL%"

echo.
if not "%ERR%"=="0" ( echo [ERROR] Test failed. See output above. ) else ( echo [OK] Test complete. )
pause
exit /b %ERR%
