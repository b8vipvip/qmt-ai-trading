#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.api_gateway.server import run_server, validate_host, DEFAULT_HOST, DEFAULT_PORT, make_handler
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--host',default=DEFAULT_HOST); p.add_argument('--port',type=int,default=DEFAULT_PORT); p.add_argument('--dry-run',action='store_true')
    a=p.parse_args(argv)
    if not validate_host(a.host): print('WARN: non-localhost host refused for Stage61 API Gateway'); return 1
    if a.dry_run: make_handler(a.repo_root); print(f'API Gateway dry-run ok host={a.host} port={a.port} read_only=True dry_run_only=True no_trade_authorization=True no_task_registered=True'); return 0
    run_server(a.repo_root,a.host,a.port); return 0
if __name__=='__main__': raise SystemExit(main())
