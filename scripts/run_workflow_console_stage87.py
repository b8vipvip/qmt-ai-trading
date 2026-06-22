from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.console_api.workflow_console import write_workflow_outputs

def main():
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--output-dir',default='local_console_workflow_stage87'); a=p.parse_args()
    print(json.dumps(write_workflow_outputs(a.repo_root,a.output_dir),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
