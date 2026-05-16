@echo off
REM Double-click or: run_sara.bat   — starts SARA CONTROL local web/API
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_sara.ps1" %*
if errorlevel 1 pause
