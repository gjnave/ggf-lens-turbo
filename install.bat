@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo Get Going Fast | Lens Turbo | Conda Installer
echo =============================================
echo.

:: Check for conda
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Conda not found. Please install Miniconda or Anaconda first.
    pause
    exit /b 1
)

:: Define environment directory
set "ENV_DIR=%CD%\environments\conda"

:: Create conda environment if it doesn't exist
if not exist "%ENV_DIR%" (
    echo Creating Conda environment in %ENV_DIR%...
    call conda create -p "%ENV_DIR%" python=3.11 -y
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create conda environment.
        pause
        exit /b 1
    )
) else (
    echo Conda environment already exists.
)

:: Activate environment
echo Activating environment...
call conda activate "%ENV_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate conda environment.
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip wheel
python -m pip install setuptools==70.2.0
python -m pip install "torch>=2.4.0,<2.6" torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install torch with cu124, trying default...
    python -m pip install torch torchvision torchaudio
)

if exist "requirements.txt" (
    python -m pip install -r requirements.txt
) else (
    echo [ERROR] requirements.txt not found.
    pause
    exit /b 1
)

:: Download models
if exist "download-models.bat" (
    echo Downloading models...
    call download-models.bat
)

echo.
echo Install complete! Use run.bat to start the app.
pause
exit /b 0

:error
echo [ERROR] An error occurred during installation.
pause
exit /b 1
