@echo off
title SARA — First-Time Setup
echo ====================================================
echo   SARA — First-Time Setup
echo ====================================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found!
    echo.
    echo   Please install Python 3.10+ from https://python.org
    echo   IMPORTANT: Check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

:: Create local venv so we don't pollute the system
echo [1/3] Creating local Python environment...
if not exist "venv" (
    python -m venv venv
    echo   Created venv\
) else (
    echo   venv\ already exists, skipping.
)

:: Activate and install
echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat

python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q

echo.
echo [3/3] Checking for AI model...

:: Check if any model is available
python -c "from sara_sdk.local_llm_sdk import discover_models; m=discover_models(); print(f'  Found {len(m)} model(s)') if m else print('  No models found yet.')"

if not exist "models\*.gguf" (
    if not exist "%USERPROFILE%\.ollama\models\manifests" (
        echo.
        echo   [INFO] No AI model found. Run SARA_GET_MODEL.bat to download one.
        echo   Recommended for this machine: TinyLlama (700MB) or Phi-3-mini (2.3GB)
    )
)

echo.
echo ====================================================
echo   Setup complete! Run SARA_RUN.bat to start SARA.
echo ====================================================
echo.
pause
