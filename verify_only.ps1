# Run from SARA folder:  .\verify_only.ps1
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$log = Join-Path $PSScriptRoot "verify_last_run.log"
"SARA verify $(Get-Date)" | Out-File -FilePath $log -Encoding utf8
"`n--- smoke_office_files ---`n" | Out-File -FilePath $log -Append -Encoding utf8
python tools\smoke_office_files.py 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
"`n--- verify_dispatch ---`n" | Out-File -FilePath $log -Append -Encoding utf8
python verify_dispatch.py 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
Write-Host "Wrote log: $log`n"
Get-Content $log
Write-Host "`nPress Enter to close."
Read-Host | Out-Null
