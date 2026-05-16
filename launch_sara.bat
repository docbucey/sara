@echo off
title SARA
echo ====================================================
echo   SARA — Starting up...
echo ====================================================
echo.

cd /d "%~dp0"

:: Check Ollama
where ollama >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [OK] Ollama found
) else (
    echo [WARN] Ollama not found — AI prompts will return errors
    echo        Install from https://ollama.com or set SARA_OLLAMA_MODEL
)

:: Check Python deps
python -c "import docx, openpyxl" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing office suite dependencies...
    pip install python-docx openpyxl python-pptx fpdf2 Pillow -q
)

:: Check local LLM
python -c "import llama_cpp" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing local LLM engine (this may take a minute)...
    pip install llama-cpp-python -q
)

echo.
echo [SARA] Starting HTTP server + Web UI...
echo [SARA] Open http://127.0.0.1:5050/ in your browser
echo [SARA] Press Ctrl+C to stop
echo.

python sara_control/server_con.py --http
pause
