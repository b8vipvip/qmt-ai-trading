$ErrorActionPreference = "Stop"
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_stage88_datahub_real_cache.py
py -m pytest tests/test_stage88_research_from_real_cache.py
py -m pytest tests/test_stage88_strategy_dry_run.py
py -m pytest tests/test_stage88_risk_gate.py
py -m pytest tests/test_stage88_workflow_frontend.py
py -m pytest tests/test_stage88_safety.py
py scripts/run_stage88_real_data_dry_run.py --repo-root . --symbols 510300.SH,510500.SH,588000.SH --period 1d --limit 60 --dry-run --read-only
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status
