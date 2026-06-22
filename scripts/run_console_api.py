from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.console_api.api_server import run_server, DEFAULT_HOST, DEFAULT_PORT
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--host',default=DEFAULT_HOST); p.add_argument('--port',type=int,default=DEFAULT_PORT); p.add_argument('--static-dir',default='local_console_app')
    a=p.parse_args(); run_server(a.host,a.port,a.static_dir)
