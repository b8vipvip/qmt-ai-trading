$ErrorActionPreference = "Stop"
Write-Host "Stage81 validation started"
$RunQmtTasks = "D:\AI\run_qmt_tasks.ps1"
if (Test-Path $RunQmtTasks) {
  $content = Get-Content -Raw -Path $RunQmtTasks
  if ($content -match "Start-Transcript" -or $content -match "验收日志已保存到") { Write-Host "run_qmt_tasks.ps1 logging marker found" } else { Write-Warning "run_qmt_tasks.ps1 logging marker missing" }
} else { Write-Warning "D:\AI\run_qmt_tasks.ps1 not found; read-only check only" }
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_console_api_stage77.py
py -m pytest tests/test_console_frontend_stage77.py
py -m pytest tests/test_ai_provider_stage78.py
py -m pytest tests/test_console_ai_frontend_stage78.py
py -m pytest tests/test_factor_research_stage79.py
py -m pytest tests/test_console_factor_frontend_stage79.py
py -m pytest tests/test_factor_strategy_stage80.py
py -m pytest tests/test_console_strategy_frontend_stage80.py
py -m pytest tests/test_run_qmt_tasks_logging_stage80.py
py -m pytest tests/test_agent_research_stage81.py
py -m pytest tests/test_console_agent_frontend_stage81.py
py -m pytest tests/test_agent_safety_stage81.py
py scripts\run_agent_research_stage81.py --repo-root . --output-dir local_console_agent_stage81
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status
