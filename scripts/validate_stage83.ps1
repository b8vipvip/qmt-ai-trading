$ErrorActionPreference = "Stop"
Write-Host "Stage83 validation: read-only checks; console output only."
py -m compileall -q qmt_ai_trading
py scripts\run_monitoring_stage83.py --repo-root . --output-dir local_console_monitoring_stage83
py -m pytest tests/test_monitoring_stage83.py tests/test_console_monitoring_frontend_stage83.py tests/test_monitoring_safety_stage83.py
$runPath = "D:\AI\run_qmt_tasks.ps1"
if (Test-Path $runPath) { Select-String -Path $runPath -Pattern "QMT_TASK_LOGGING_STAGE80" -SimpleMatch | ForEach-Object { Write-Host $_.Line } } else { Write-Host "run_qmt_tasks.ps1 not found; read-only check only." }
