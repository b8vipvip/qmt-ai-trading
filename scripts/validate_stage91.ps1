$ErrorActionPreference = "Stop"
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_stage91_account_readonly_config.py
py -m pytest tests/test_stage91_account_masking.py
py -m pytest tests/test_stage91_rate_limit.py
py -m pytest tests/test_stage91_account_readonly_provider.py
py -m pytest tests/test_stage91_frontend.py
py -m pytest tests/test_stage91_safety.py
py scripts/run_account_readonly_stage91.py --repo-root . --output-dir local_console_account_stage91 --dry-run --read-only
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status
