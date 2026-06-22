$ErrorActionPreference = "Stop"
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_stage90_xttrader_config.py
py -m pytest tests/test_stage90_import_guard.py
py -m pytest tests/test_stage90_capability_probe.py
py -m pytest tests/test_stage90_order_preview.py
py -m pytest tests/test_stage90_frontend.py
py -m pytest tests/test_stage90_safety.py
py scripts/run_xttrader_boundary_stage90.py --repo-root . --input-stage 89 --output-dir local_console_xttrader_stage90 --dry-run --read-only
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status
