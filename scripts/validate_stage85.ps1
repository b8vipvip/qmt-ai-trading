$ErrorActionPreference = "Stop"
Write-Host "Stage85 validation started"
$runQmt = "D:\AI\run_qmt_tasks.ps1"
if (Test-Path $runQmt) {
  $text = Get-Content -LiteralPath $runQmt -Raw -ErrorAction Stop
  if ($text -match "QMT_TASK_LOG" -or $text -match "validation") { Write-Host "run_qmt_tasks.ps1 marker found" } else { Write-Host "run_qmt_tasks.ps1 marker missing" }
} else {
  Write-Host "run_qmt_tasks.ps1 missing; read-only check only"
}
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_xtdata_boundary_stage85.py
py -m pytest tests/test_console_xtdata_frontend_stage85.py
py -m pytest tests/test_xtdata_boundary_safety_stage85.py
py scripts/run_xtdata_boundary_stage85.py --repo-root . --output-dir local_console_xtdata_stage85
Write-Host "Stage85 validation completed"
