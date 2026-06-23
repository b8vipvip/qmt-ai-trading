$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogDir = "validation_logs"
$ReportDir = "artifacts\reports\console_validation"
New-Item -ItemType Directory -Force $LogDir | Out-Null
New-Item -ItemType Directory -Force $ReportDir | Out-Null
$LogPath = Join-Path $LogDir "project_validation_$Stamp.log"
$JsonPath = Join-Path $ReportDir "latest_project_validation.json"
$MdPath = Join-Path $ReportDir "latest_project_validation.md"
"QMT AI unified project validation started" | Tee-Object -FilePath $LogPath -Append
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\validate_console_unified.ps1" 2>&1 | Tee-Object -FilePath $LogPath -Append
$Code = $LASTEXITCODE
$Status = if ($Code -eq 0) { "PASS" } else { "FAILED" }
$result = [pscustomobject]@{
    ok = ($Code -eq 0)
    status = $Status
    exit_code = $Code
    generated_at = (Get-Date).ToString("s")
    log_path = $LogPath
    validation_entry = "scripts\\validate_project.ps1"
    no_stage_development = $true
    unified_api_prefix = "/api/v1"
    unified_frontend = "local_console_app"
    safety = @{ read_only = $true; dry_run = $true; live_disabled = $true; no_order_submitted = $true; order_submit_enabled = $false; order_cancel_enabled = $false; real_order_submitted = $false }
}
$result | ConvertTo-Json -Depth 8 | Set-Content -Path $JsonPath -Encoding UTF8
("# QMT AI Unified Project Validation`n`nStatus: {0}`n`nLog: {1}`n`nEntry: scripts\validate_project.ps1" -f $Status, $LogPath) | Set-Content -Path $MdPath -Encoding UTF8
if ($Code -ne 0) { exit $Code }
exit 0
