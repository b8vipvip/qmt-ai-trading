from __future__ import annotations
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.trading_gateway import run_xttrader_boundary_stage90

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root', default='.')
    p.add_argument('--input-stage', type=int, default=89)
    p.add_argument('--output-dir', default='local_console_xttrader_stage90')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--read-only', action='store_true')
    args=p.parse_args()
    print(run_xttrader_boundary_stage90(args.repo_root,args.input_stage,args.output_dir,True,True))
if __name__=='__main__': main()
