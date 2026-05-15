$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = "C:/Users/mdbuc/AppData/Local/Python/pythoncore-3.14-64/python.exe"
$appPath = Join-Path $scriptDir "app.py"

$env:SARA_LOCAL_ONLY = "1"
$env:SARA_ENFORCE_AUTH_ALL = "0"
if (-not $env:SARA_ENVOY_SECRET) {
    $env:SARA_ENVOY_SECRET = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
}
if (-not $env:SARA_REVEAL_WINDOW_MINUTES) {
    $env:SARA_REVEAL_WINDOW_MINUTES = "20"
}

Write-Host "Launching SARA in local-only browser mode..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8787/dashboard"
& $pythonExe $appPath
