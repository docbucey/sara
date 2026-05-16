@echo off
title SARA — Build Portable Package
echo ====================================================
echo   SARA — Building portable thumb-drive package
echo ====================================================
echo.

cd /d "%~dp0"

set "OUT=%~dp0SARA_PORTABLE"

if exist "%OUT%" (
    echo [WARN] %OUT% already exists. Delete it first or it will be updated in place.
    echo.
)

:: Create folder structure
mkdir "%OUT%" 2>nul
mkdir "%OUT%\models" 2>nul
mkdir "%OUT%\sara_common" 2>nul
mkdir "%OUT%\sara_core" 2>nul
mkdir "%OUT%\sara_control" 2>nul
mkdir "%OUT%\sara_mama" 2>nul
mkdir "%OUT%\sara_security" 2>nul
mkdir "%OUT%\sara_sdk" 2>nul
mkdir "%OUT%\sara_web" 2>nul

:: Copy SARA source
echo [1/6] Copying SARA source...
xcopy /E /Y /Q "sara_common\*" "%OUT%\sara_common\" >nul 2>nul
xcopy /E /Y /Q "sara_core\*" "%OUT%\sara_core\" >nul 2>nul
xcopy /E /Y /Q "sara_control\*" "%OUT%\sara_control\" >nul 2>nul
xcopy /E /Y /Q "sara_mama\*" "%OUT%\sara_mama\" >nul 2>nul
xcopy /E /Y /Q "sara_security\*" "%OUT%\sara_security\" >nul 2>nul
xcopy /E /Y /Q "sara_sdk\*" "%OUT%\sara_sdk\" >nul 2>nul
if exist "sara_web" xcopy /E /Y /Q "sara_web\*" "%OUT%\sara_web\" >nul 2>nul
copy /Y "requirements.txt" "%OUT%\" >nul
copy /Y "actionmap.updated.json" "%OUT%\" >nul 2>nul

:: Copy launchers
echo [2/6] Copying launchers...
copy /Y "SARA_RUN.bat" "%OUT%\" >nul 2>nul
copy /Y "SARA_SETUP.bat" "%OUT%\" >nul 2>nul
copy /Y "SARA_GET_MODEL.bat" "%OUT%\" >nul 2>nul

:: Copy models if any .gguf files exist
echo [3/6] Checking for local models...
set "MODEL_COUNT=0"
for %%f in (models\*.gguf) do (
    echo   Copying %%~nxf (this may take a while for large models)...
    copy /Y "%%f" "%OUT%\models\" >nul
    set /a MODEL_COUNT+=1
)

:: Check Ollama cache for models to offer
echo [4/6] Checking Ollama cache...
if exist "%USERPROFILE%\.ollama\models\manifests" (
    echo   Ollama models found. They will be auto-detected at runtime.
    echo   To make the package fully standalone, run SARA_GET_MODEL.bat
    echo   to download a small model into the models\ folder.
) else (
    echo   No Ollama cache found.
)

:: Create the portable launchers inside the output
echo [5/6] Writing portable launcher scripts...

:: -- SARA_RUN.bat is written by build, see below --
:: -- SARA_SETUP.bat is written by build, see below --

echo [6/6] Done!
echo.
echo ====================================================
echo   Portable package ready at:
echo   %OUT%
echo.
echo   To deploy:
echo     1. Copy SARA_PORTABLE folder to thumb drive
echo     2. On target PC: run SARA_SETUP.bat (once)
echo     3. Then run SARA_RUN.bat to start SARA
echo ====================================================
echo.
pause
