$ErrorActionPreference = "Stop"
Write-Host "Stage87 validation: read-only checks only"
$repo = Split-Path -Parent $PSScriptRoot
$runQmt = "D:\AI\run_qmt_tasks.ps1"
if (Test-Path $runQmt) {
  $content = Get-Content -LiteralPath $runQmt -Raw
  $hasMarker = $content.Contains("VALIDATION_LOG") -or $content.Contains("run_qmt_tasks")
  Write-Host "run_qmt_tasks.ps1 exists: True"
  Write-Host "run_qmt_tasks.ps1 marker present: $hasMarker"
} else {
  Write-Host "run_qmt_tasks.ps1 exists: False"
}
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_xtdata_live_readonly_stage87.py tests/test_console_xtdata_live_frontend_stage87.py tests/test_xtdata_live_safety_stage87.py tests/test_artifact_paths_stage87.py tests/test_artifact_migration_stage87.py tests/test_console_artifact_migration_frontend_stage87.py
py scripts\run_xtdata_live_stage87.py --repo-root . --output-dir local_console_xtdata_live_stage87
py scripts\run_artifact_migration_stage87.py --repo-root . --output-dir local_console_artifact_migration_stage87
Write-Host "Stage87 validation complete"
