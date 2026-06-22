from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.market_gateway import run_xtdata_live_stage87
p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_xtdata_live_stage87')
p.add_argument('--enable-xtdata',action='store_true'); p.add_argument('--allow-import-xtdata',action='store_true'); p.add_argument('--allow-real-market-data',action='store_true'); p.add_argument('--allow-connect-miniqmt',action='store_true')
p.add_argument('--symbols',default='510300.SH,510500.SH,588000.SH'); p.add_argument('--period',default='1d'); p.add_argument('--limit',type=int,default=100)
a=p.parse_args(); print(json.dumps(run_xtdata_live_stage87(a.repo_root,a.output_dir,enabled=a.enable_xtdata,allow_import_xtdata=a.allow_import_xtdata,allow_real_market_data=a.allow_real_market_data,allow_connect_miniqmt=a.allow_connect_miniqmt,symbols=[x.strip() for x in a.symbols.split(',') if x.strip()],period=a.period,limit=a.limit),ensure_ascii=False,indent=2,sort_keys=True))
