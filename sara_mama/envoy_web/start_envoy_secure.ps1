$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = "C:/Users/mdbuc/AppData/Local/Python/pythoncore-3.14-64/python.exe"
$appPath = Join-Path $scriptDir "app.py"

Write-Host "SARA Envoy Secure Launcher" -ForegroundColor Cyan

$username = Read-Host "Enter SARA username"
if ([string]::IsNullOrWhiteSpace($username)) {
    throw "Username cannot be empty."
}

$securePassword = Read-Host "Enter SARA password" -AsSecureString
if (-not $securePassword) {
    throw "Password cannot be empty."
}
$plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
)

$secretInput = Read-Host "Optional secret (leave blank to auto-generate)"
if ([string]::IsNullOrWhiteSpace($secretInput)) {
    $secretInput = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
}

$windowInput = Read-Host "Reveal window minutes (default 20)"
if ([string]::IsNullOrWhiteSpace($windowInput)) {
    $windowInput = "20"
}

$env:SARA_ENVOY_USERNAME = $username
$env:SARA_ENVOY_PASSWORD = $plainPassword
$env:SARA_ENVOY_SECRET = $secretInput
$env:SARA_REVEAL_WINDOW_MINUTES = $windowInput

Write-Host "Starting SARA Envoy on http://127.0.0.1:8787/login" -ForegroundColor Green
& $pythonExe $appPath
