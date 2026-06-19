#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_gray_ledger.models import LiveGrayLedgerDecision
from qmt_ai_trading.live_gray_ledger.service import build_default_live_gray_ledger_config, run_live_gray_ledger, save_live_gray_ledger_report

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage41 read-only live gray ledger.')
    p.add_argument('--repo-root', default='.')
    p.add_argument('--output-dir', default='live_gray_ledger_stage41')
    p.add_argument('--redline-review-dir', default='redline_review_stage40')
    p.add_argument('--final-authorization-dir', default='final_authorization_stage40')
    p.add_argument('--live-env-check-dir', default='live_env_check_stage40')
    p.add_argument('--live-manual-prep-dir', default='live_manual_prep_stage40')
    p.add_argument('--json-output', default=None)
    p.add_argument('--output', default=None)
    a=p.parse_args(argv)
    out=a.output or str(Path(a.output_dir)/'live_gray_ledger.md')
    jout=a.json_output or str(Path(a.output_dir)/'live_gray_ledger.json')
    cfg=build_default_live_gray_ledger_config(repo_root=a.repo_root, output_dir=a.output_dir, redline_review_dir=a.redline_review_dir, final_authorization_dir=a.final_authorization_dir, live_env_check_dir=a.live_env_check_dir, live_manual_prep_dir=a.live_manual_prep_dir)
    report=run_live_gray_ledger(cfg)
    save_live_gray_ledger_report(report, out, jout)
    print(f"Stage41 live gray read-only ledger written: {out}")
    print(f"Stage41 live gray read-only ledger JSON written: {jout}")
    print(f"Decision: {getattr(report.decision,'value',report.decision)}")
    return 1 if report.decision == LiveGrayLedgerDecision.BLOCKED else 0
if __name__=='__main__': raise SystemExit(main())
