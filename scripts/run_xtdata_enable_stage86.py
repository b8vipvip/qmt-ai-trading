from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.market_gateway import run_xtdata_enable_stage86
p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_xtdata_enable_stage86')
a=p.parse_args(); print(json.dumps(run_xtdata_enable_stage86(a.repo_root,a.output_dir),ensure_ascii=False,indent=2,sort_keys=True))
