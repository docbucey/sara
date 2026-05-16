# SARA — start CONTROL + local web/API (good-enough default).
# Bridge / transport redesign is separate; this only launches what already works.
#
#   .\run_sara.ps1
#   .\run_sara.ps1 -Port 5051
#   .\run_sara.ps1 -BindHost 127.0.0.1 -Port 5050
#
# Requires: Python 3.10+; for a full feature set use `pip install -r requirements.txt`.

param(
    [int] $Port = 5050,
    [string] $BindHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

$venvPy = Join-Path $Root "venv\Scripts\python.exe"
$python = if (Test-Path $venvPy) { $venvPy } else { "python" }

$server = Join-Path $Root "sara_control\server_con.py"
if (-not (Test-Path $server)) {
    Write-Error "Not found: $server"
}

Write-Host "[SARA] Root: $Root"
Write-Host "[SARA] Python: $python"
Write-Host "[SARA] http://${BindHost}:$Port/  (health: /health , API: POST /shunt)"
Write-Host "[SARA] Ctrl+C to stop."
Write-Host ""

& $python $server --http --host $BindHost --port $Port
