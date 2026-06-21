$ErrorActionPreference = "Stop"
function Print-File([string]$Path) { Get-Content -LiteralPath $Path -Encoding UTF8 | Write-Host }
function Check-NoBackup([string]$Dir,[string]$Pattern,[string]$Label,[string]$Kind) { if (Get-ChildItem -Path $Dir -Filter $Pattern -ErrorAction SilentlyContinue) { throw "$Label $Kind backup files found" } }
function Clean-PythonCache { Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Get-ChildItem -Path . -Recurse -Directory -Filter .pytest_cache | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue }
powershell -ExecutionPolicy Bypass -File .\scripts\install_run_qmt_tasks_logging.ps1
$parentRunScript = Join-Path (Split-Path -Parent (Get-Location)) "run_qmt_tasks.ps1"
$runText = Get-Content -LiteralPath $parentRunScript -Raw -Encoding UTF8
foreach ($marker in @('validation_logs','stage${stage}_validation_','Start-Transcript','Stop-Transcript','验收日志已保存到')) { if ($runText -notlike "*$marker*") { throw "run_qmt_tasks logging marker missing: $marker" } }
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
py scripts\run_factor_strategy_review.py --repo-root . --factor-dir local_console_factor_stage79 --output-dir local_console_strategy_stage80 --app-dir local_console_app_stage77
Print-File local_console_strategy_stage80\factor_strategy_signals.md
Print-File local_console_strategy_stage80\factor_trade_intents.md
Print-File local_console_strategy_stage80\factor_risk_decisions.md
Print-File local_console_strategy_stage80\factor_strategy_report.md
Print-File local_console_strategy_stage80\frontend_strategy_contract.md
Print-File local_console_strategy_stage80\next_agent_research_plan.md
Print-File local_console_strategy_stage80\run_qmt_tasks_logging_fix_report.md
py scripts\check_stage53_roadmap_plan.py
Check-NoBackup scripts validate_stage79.ps1.bak_stage79fix_* Stage79 validate
Check-NoBackup scripts validate_stage80.ps1.bak_stage80fix_* Stage80 validate
Clean-PythonCache
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status
