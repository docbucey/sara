# Build a portable SARA.exe (self-contained, no separate .NET install on target PC).
# From this folder in PowerShell (if scripts blocked, use publish_sara.bat instead):
#   .\publish_sara.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$out = Join-Path $PSScriptRoot "publish\win-x64"
Write-Host "Publishing to: $out"
dotnet publish .\DisabilityMapper.csproj -c Release -r win-x64 `
    --self-contained true `
    -p:PublishSingleFile=true `
    -p:IncludeNativeLibrariesForSelfExtract=true `
    -o $out

Write-Host ""
Write-Host "Output: $(Join-Path $out 'SARA.exe')"
if (Test-Path (Join-Path $out "SARA.exe")) {
    Start-Process explorer.exe $out
}
