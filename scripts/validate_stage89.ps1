$ErrorActionPreference = "Stop"
py -m compileall -q qmt_ai_trading
py -m pytest tests/test_stage89_paper_broker.py
py -m pytest tests/test_stage89_position_book.py
py -m pytest tests/test_stage89_pnl_tracker.py
py -m pytest tests/test_stage89_risk_replay.py
py -m pytest tests/test_stage89_frontend.py
py -m pytest tests/test_stage89_safety.py
py scripts/run_paper_trading_stage89.py --repo-root . --input-stage 88 --output-dir local_console_paper_stage89 --dry-run --read-only
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan
powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status
