from __future__ import annotations
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.paper_trading import run_paper_trading_stage89
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--repo-root',default='.'); ap.add_argument('--input-stage',default='88'); ap.add_argument('--output-dir',default='local_console_paper_stage89'); ap.add_argument('--dry-run',action='store_true'); ap.add_argument('--read-only',action='store_true')
    args=ap.parse_args(); print(run_paper_trading_stage89(args.repo_root,args.input_stage,args.output_dir,args.dry_run,args.read_only))
