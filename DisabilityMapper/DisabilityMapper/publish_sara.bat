@echo off
cd /d "%~dp0"
echo Publishing SARA.exe (may take a few minutes the first time)...
dotnet publish .\DisabilityMapper.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o "%~dp0publish\win-x64"
if errorlevel 1 (
  echo dotnet publish failed.
  pause
  exit /b 1
)
echo.
echo Done. EXE is here:
echo   %~dp0publish\win-x64\SARA.exe
explorer "%~dp0publish\win-x64"
pause
