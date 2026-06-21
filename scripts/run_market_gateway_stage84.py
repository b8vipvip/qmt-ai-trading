from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.market_gateway import run_market_gateway_stage84
p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_market_stage84'); p.add_argument('--provider',default='mock_provider'); p.add_argument('--symbols',nargs='*',default=['510300.SH','510500.SH','588000.SH']); p.add_argument('--timeframe',default='1d'); p.add_argument('--limit',type=int,default=20); p.add_argument('--speed',type=float,default=1.0)
a=p.parse_args(); print(json.dumps(run_market_gateway_stage84(a.repo_root,a.output_dir,a.provider,a.symbols,a.timeframe,a.limit,a.speed),ensure_ascii=False,indent=2,sort_keys=True))
