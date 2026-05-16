@echo off
REM Build SARA.exe from the desktop shell (DisabilityMapper) — run this from the SARA repo.
set "MAPPER=%~dp0..\disabilitymapper\DisabilityMapper"
if not exist "%MAPPER%\DisabilityMapper.csproj" (
  echo Could not find DisabilityMapper at:
  echo   %MAPPER%
  echo Set MAPPER_ROOT to your DisabilityMapper folder and run again, or move the project under SARA.
  pause
  exit /b 1
)
call "%MAPPER%\publish_sara.bat"
