$ErrorActionPreference = "Stop"
function Print-File($Path) { Write-Host "`n===== $Path ====="; Get-Content -Encoding UTF8 $Path }
function Clean-PythonCache { Get-ChildItem -Path . -Recurse -Directory -Force -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Get-ChildItem -Path . -Recurse -Directory -Force -Filter .pytest_cache | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue }
function Check-NoBackup($Dir,$Pattern,$Label,$Kind) { $hits = Get-ChildItem -Path $Dir -Filter $Pattern -ErrorAction SilentlyContinue; if ($hits) { throw "$Label $Kind backup files found" } }
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_local_console_refresh_stage68.py
py -m pytest tests/test_local_console_grouping_stage69.py
py -m pytest tests/test_local_console_drilldown_stage70.py
py -m pytest tests/test_local_console_review_stage71.py
py -m pytest tests/test_local_console_acceptance_stage72.py
py -m pytest tests/test_local_console_help_stage73.py
py -m pytest tests/test_local_console_demo_stage74.py
py -m pytest tests/test_ui_productization_closure_stage75.py
py -m pytest tests/test_stage76_roadmap_review.py
py -m pytest tests/test_console_api_stage77.py
py -m pytest tests/test_console_frontend_stage77.py
py scripts\run_local_console_business_console.py --repo-root . --output-dir local_console_app_stage77 --closure-dir local_console_closure_stage75 --roadmap-dir stage76_roadmap_review
Print-File local_console_app_stage77\README.md
Print-File local_console_app_stage77\local_console_business_console_report.md
Print-File local_console_app_stage77\frontend_api_contract.md
Print-File local_console_app_stage77\task_catalog.md
Print-File local_console_app_stage77\integration_check_report.md
Print-File local_console_app_stage77\next_pre_live_safety_audit_plan.md
py scripts\check_stage53_roadmap_plan.py
Check-NoBackup scripts validate_stage76.ps1.bak_stage76fix_* Stage76 validate
Check-NoBackup scripts validate_stage77.ps1.bak_stage77fix_* Stage77 validate
Clean-PythonCache
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status
