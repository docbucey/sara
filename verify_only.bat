@echo off
setlocal
echo In PowerShell you MUST type:  .\verify_only.bat
echo Or use:  .\verify_only.ps1
echo.
cd /d "%~dp0"
set "LOG=%~dp0verify_last_run.log"
del "%LOG%" 2>nul
echo SARA verify %date% %time% 1>"%LOG%"
echo. 1>>"%LOG%"
echo --- smoke_office_files --- 1>>"%LOG%"
python tools\smoke_office_files.py 1>>"%LOG%" 2>>&1
echo. 1>>"%LOG%"
echo --- verify_dispatch --- 1>>"%LOG%"
python verify_dispatch.py 1>>"%LOG%" 2>>&1
echo. 1>>"%LOG%"
echo Wrote log: %LOG%
type "%LOG%"
echo.
pause
