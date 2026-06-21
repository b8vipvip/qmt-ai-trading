$ErrorActionPreference = "Stop"
function Print-File([string]$Path) { Get-Content -LiteralPath $Path -Encoding UTF8 | Write-Host }
function Check-NoBackup([string]$Dir,[string]$Pattern,[string]$Label,[string]$Kind) { if (Get-ChildItem -Path $Dir -Filter $Pattern -ErrorAction SilentlyContinue) { throw "$Label $Kind backup files found" } }
function Clean-PythonCache { Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Get-ChildItem -Path . -Recurse -Directory -Filter .pytest_cache | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue }
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_console_api_stage77.py
py -m pytest tests/test_console_frontend_stage77.py
py -m pytest tests/test_ai_provider_stage78.py
py -m pytest tests/test_console_ai_frontend_stage78.py
py scripts\run_ai_provider_review.py --repo-root . --output-dir local_console_ai_stage78 --app-dir local_console_app_stage77
Print-File local_console_ai_stage78\ai_model_discovery_report.md
Print-File local_console_ai_stage78\ai_model_stress_test_report.md
Print-File local_console_ai_stage78\ai_model_usage_draft.md
Print-File local_console_ai_stage78\frontend_ai_contract.md
Print-File local_console_ai_stage78\next_factor_strategy_visualization_plan.md
py scripts\check_stage53_roadmap_plan.py
Check-NoBackup scripts validate_stage77.ps1.bak_stage77fix_* Stage77 validate
Check-NoBackup scripts validate_stage78.ps1.bak_stage78fix_* Stage78 validate
Clean-PythonCache
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status
