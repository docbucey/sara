@echo off
title SARA
echo ====================================================
echo   SARA — Starting up...
echo ====================================================
echo.

cd /d "%~dp0"

:: Use local venv if it exists (portable), otherwise system Python
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Using local environment
) else (
    echo [OK] Using system Python
)

:: Quick dep check
python -c "import docx, openpyxl" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt -q
)

:: Show what model will be used
echo.
python -c "from sara_sdk.local_llm_sdk import discover_models; ms=discover_models(); print(f'[AI] {len(ms)} model(s) available: ' + ', '.join(m['name'] for m in ms[:5])) if ms else print('[AI] No local models — AI prompts will use Ollama or return errors')"
echo.

echo [SARA] Starting HTTP server...
echo [SARA] Open http://127.0.0.1:5050/ in your browser
echo [SARA] C# DisabilityMapper connects automatically via Bucey Shunt
echo [SARA] Press Ctrl+C to stop
echo.

python sara_control/server_con.py --http
pause
