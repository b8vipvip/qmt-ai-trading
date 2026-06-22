from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.trading_gateway.account_readonly_report import run_account_readonly_stage91

def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_account_stage91')
    p.add_argument('--enable-account-readonly',action='store_true'); p.add_argument('--allow-import-xttrader',action='store_true'); p.add_argument('--allow-connect-trade-session',action='store_true'); p.add_argument('--allow-account-query',action='store_true'); p.add_argument('--allow-position-query',action='store_true'); p.add_argument('--manual-confirmed',action='store_true'); p.add_argument('--dry-run',action='store_true'); p.add_argument('--read-only',action='store_true')
    a=p.parse_args(); print(run_account_readonly_stage91(a.repo_root,a.output_dir,a.enable_account_readonly,a.allow_import_xttrader,a.allow_connect_trade_session,a.allow_account_query,a.allow_position_query,a.manual_confirmed,True,True))
if __name__=='__main__': main()
