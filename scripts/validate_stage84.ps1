$ErrorActionPreference = "Stop"
Write-Host "Stage84 validation: read-only checks, compile, tests, and sandbox market report generation."
$runQmt = "D:\AI\run_qmt_tasks.ps1"
if (Test-Path $runQmt) { Write-Host "run_qmt_tasks.ps1 exists; read-only marker check only."; Select-String -Path $runQmt -Pattern "validation log|logging|marker" -SimpleMatch | Select-Object -First 3 | ForEach-Object { Write-Host $_.Line } } else { Write-Host "run_qmt_tasks.ps1 not found; read-only fallback." }
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_market_gateway_stage84.py tests/test_console_market_frontend_stage84.py tests/test_market_gateway_safety_stage84.py
py scripts/run_market_gateway_stage84.py --repo-root . --output-dir local_console_market_stage84
