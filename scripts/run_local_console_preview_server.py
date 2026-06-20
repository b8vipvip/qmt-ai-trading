from __future__ import annotations
import argparse, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qmt_ai_trading.local_console.preview_models import LocalConsolePreviewConfig
from qmt_ai_trading.local_console.preview_service import run_local_console_preview_review
from qmt_ai_trading.local_console.preview_server import run_preview_server_once
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--repo-root',default='.'); p.add_argument('--static-dir',default='local_console_binding_stage66'); p.add_argument('--host',default='127.0.0.1'); p.add_argument('--port',type=int,default=8767); p.add_argument('--dry-run',action='store_true'); p.add_argument('--serve-once',action='store_true'); p.add_argument('--timeout-seconds',type=int,default=5)
    # accept report args for compatibility
    for a in ['output','json-output','route-output','route-json-output','static-output','static-json-output','response-output','response-json-output','safety-output','safety-json-output','plan-output','plan-json-output']: p.add_argument('--'+a, default=None)
    ns=p.parse_args(argv); cfg=LocalConsolePreviewConfig(ns.repo_root,ns.static_dir,ns.host,ns.port,True,ns.serve_once,ns.timeout_seconds)
    r=run_local_console_preview_review(cfg)
    if ns.serve_once: run_preview_server_once(cfg)
    print(r.decision.value); return 0 if ns.dry_run or ns.serve_once else 0
if __name__=='__main__': raise SystemExit(main())
