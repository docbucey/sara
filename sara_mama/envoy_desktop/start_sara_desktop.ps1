$ErrorActionPreference = "Stop"

$desktopDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$webDir = Join-Path (Split-Path -Parent $desktopDir) "envoy_web"
$webApp = Join-Path $webDir "app.py"
$desktopApp = Join-Path $desktopDir "sara_desktop_app.py"

function Resolve-PythonExe {
    function Test-CandidateModules {
        param(
            [string]$Candidate,
            [bool]$UsePyLauncher = $false
        )
        $check = "import flask, requests, PySide6"
        try {
            if ($UsePyLauncher) {
                & py -3 -c $check *> $null
            } else {
                & $Candidate -c $check *> $null
            }
            return ($LASTEXITCODE -eq 0)
        }
        catch {
            return $false
        }
    }

    $candidates = @()
    if ($env:SARA_PYTHON_EXE) { $candidates += $env:SARA_PYTHON_EXE }
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) { $candidates += $pythonCmd.Path }
    $candidates += @(
        "C:/Users/mdbuc/AppData/Local/Python/pythoncore-3.11-64/python.exe",
        "C:/Users/mdbuc/AppData/Local/Python/pythoncore-3.14-64/python.exe"
    )

    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) {
            if (Test-CandidateModules -Candidate $c) {
                return $c
            }
        }
    }

    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        if (Test-CandidateModules -Candidate "py" -UsePyLauncher $true) {
            return "py"
        }
    }

    throw "No compatible Python runtime found (needs flask + requests + PySide6). Set SARA_PYTHON_EXE to the correct interpreter."
}

$pythonExe = Resolve-PythonExe
if (-not (Test-Path $webApp)) { throw "Missing web app: $webApp" }
if (-not (Test-Path $desktopApp)) { throw "Missing desktop app: $desktopApp" }

$logDir = Join-Path $desktopDir "logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backendOut = Join-Path $logDir ("backend_" + $stamp + ".out.log")
$backendErr = Join-Path $logDir ("backend_" + $stamp + ".err.log")

if ($pythonExe -eq "py") {
    $pythonArgs = @("-3", $webApp)
    $desktopArgs = @("-3", $desktopApp)
} else {
    $pythonArgs = @($webApp)
    $desktopArgs = @($desktopApp)
}

Write-Host "SARA Desktop Launch" -ForegroundColor Cyan
$username = Read-Host "Username for SARA"
if ([string]::IsNullOrWhiteSpace($username)) { $username = "md" }
$securePassword = Read-Host "Password for SARA" -AsSecureString
$plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
)
if ([string]::IsNullOrWhiteSpace($plainPassword)) { throw "Password required." }

$env:SARA_ENVOY_USERNAME = $username
$env:SARA_ENVOY_PASSWORD = $plainPassword
$env:SARA_ENVOY_BASE_URL = "http://127.0.0.1:8787"
$env:SARA_ENVOY_ENTRYPOINT = "/dashboard"
$env:SARA_LOCAL_ONLY = "1"
if (-not $env:SARA_ENVOY_SECRET) {
    $env:SARA_ENVOY_SECRET = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
}
if (-not $env:SARA_REVEAL_WINDOW_MINUTES) {
    $env:SARA_REVEAL_WINDOW_MINUTES = "20"
}

$webProc = Start-Process -FilePath $pythonExe -ArgumentList $pythonArgs -PassThru -WindowStyle Hidden -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr

$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 250
    if ($webProc.HasExited) {
        $outTail = ""
        $errTail = ""
        if (Test-Path $backendOut) { $outTail = (Get-Content $backendOut -Tail 20 | Out-String) }
        if (Test-Path $backendErr) { $errTail = (Get-Content $backendErr -Tail 20 | Out-String) }
        throw "Envoy backend exited early (code $($webProc.ExitCode)).`nOut:`n$outTail`nErr:`n$errTail"
    }
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8787/login" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) {
            $ready = $true
            break
        }
    } catch {}
}

if (-not $ready) {
    $outTail = ""
    $errTail = ""
    if (Test-Path $backendOut) { $outTail = (Get-Content $backendOut -Tail 20 | Out-String) }
    if (Test-Path $backendErr) { $errTail = (Get-Content $backendErr -Tail 20 | Out-String) }
    try { Stop-Process -Id $webProc.Id -Force } catch {}
    throw "Envoy web backend did not become ready in time.`nOut:`n$outTail`nErr:`n$errTail"
}

try {
    & $pythonExe @desktopArgs
}
finally {
    try { Stop-Process -Id $webProc.Id -Force } catch {}
}
