$ErrorActionPreference = "Stop"
function Print-File([string]$Path) { Get-Content -LiteralPath $Path -Encoding UTF8 | Write-Host }
function Check-NoBackup([string]$Dir,[string]$Pattern,[string]$Label,[string]$Kind) { if (Get-ChildItem -Path $Dir -Filter $Pattern -ErrorAction SilentlyContinue) { throw "$Label $Kind backup files found" } }
function Clean-PythonCache { Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Get-ChildItem -Path . -Recurse -Directory -Filter .pytest_cache | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue }
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_console_api_stage77.py
py -m pytest tests/test_console_frontend_stage77.py
py -m pytest tests/test_ai_provider_stage78.py
py -m pytest tests/test_console_ai_frontend_stage78.py
py -m pytest tests/test_factor_research_stage79.py
py -m pytest tests/test_console_factor_frontend_stage79.py
py -m pytest tests/test_run_qmt_tasks_logging_stage79.py
py scripts\run_factor_research_review.py --repo-root . --output-dir local_console_factor_stage79 --app-dir local_console_app_stage79
Print-File local_console_factor_stage79\factor_catalog.md
Print-File local_console_factor_stage79\factor_config_seed.md
Print-File local_console_factor_stage79\factor_results.md
Print-File local_console_factor_stage79\factor_evaluation.md
Print-File local_console_factor_stage79\factor_candidates.md
Print-File local_console_factor_stage79\factor_report.md
Print-File local_console_factor_stage79\frontend_factor_contract.md
Print-File local_console_factor_stage79\next_strategy_integration_plan.md
py scripts\check_stage53_roadmap_plan.py
Check-NoBackup scripts validate_stage78.ps1.bak_stage78fix_* Stage78 validate
Check-NoBackup scripts validate_stage79.ps1.bak_stage79fix_* Stage79 validate
Clean-PythonCache
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status
