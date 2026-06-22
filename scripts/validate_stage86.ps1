$ErrorActionPreference = "Stop"
Write-Host "Stage86 validation started"
$runQmt = "D:\AI\run_qmt_tasks.ps1"
if (Test-Path $runQmt) {
  $text = Get-Content -LiteralPath $runQmt -Raw -ErrorAction Stop
  if ($text -match "QMT_TASK_LOG" -or $text -match "validation") { Write-Host "run_qmt_tasks.ps1 marker found" } else { Write-Host "run_qmt_tasks.ps1 marker missing" }
} else {
  Write-Host "run_qmt_tasks.ps1 missing; read-only check only"
}
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_xtdata_enable_stage86.py
py -m pytest tests/test_console_xtdata_enable_frontend_stage86.py
py -m pytest tests/test_xtdata_enable_safety_stage86.py
py scripts/run_xtdata_enable_stage86.py --repo-root . --output-dir local_console_xtdata_enable_stage86
Write-Host "Stage86 validation completed"
