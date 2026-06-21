from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.backtest_dashboard import run_backtest_dashboard
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--output-dir',default='local_console_backtest_stage82'); ap.add_argument('--backtest-mode',default='mock_shadow')
    ns=ap.parse_args(); print(json.dumps(run_backtest_dashboard(ns.repo_root,ns.output_dir,ns.backtest_mode),ensure_ascii=False,indent=2))
