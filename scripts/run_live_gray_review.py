#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_gray_review.models import LiveGrayReviewDecision
from qmt_ai_trading.live_gray_review.service import build_default_live_gray_review_config, run_live_gray_review, save_live_gray_review_report, save_readonly_rehearsal_report

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage42 read-only live gray human review package.')
    p.add_argument('--repo-root', default='.')
    p.add_argument('--output-dir', default='live_gray_review_stage42')
    p.add_argument('--ledger-dir', default='live_gray_ledger_stage41')
    p.add_argument('--redline-review-dir', default='redline_review_stage40')
    p.add_argument('--final-authorization-dir', default='final_authorization_stage40')
    p.add_argument('--output', default=None)
    p.add_argument('--json-output', default=None)
    p.add_argument('--rehearsal-output', default=None)
    p.add_argument('--rehearsal-json-output', default=None)
    args=p.parse_args(argv)
    out=Path(args.output_dir)
    cfg=build_default_live_gray_review_config(args.repo_root, output_dir=str(out), ledger_dir=args.ledger_dir, redline_review_dir=args.redline_review_dir, final_authorization_dir=args.final_authorization_dir)
    report=run_live_gray_review(cfg)
    md=Path(args.output) if args.output else out/'live_gray_review.md'
    js=Path(args.json_output) if args.json_output else out/'live_gray_review.json'
    reh_md=Path(args.rehearsal_output) if args.rehearsal_output else out/'readonly_rehearsal.md'
    reh_js=Path(args.rehearsal_json_output) if args.rehearsal_json_output else out/'readonly_rehearsal.json'
    save_live_gray_review_report(report, md, js)
    save_readonly_rehearsal_report(report.rehearsal, reh_md, reh_js)  # type: ignore[arg-type]
    print(f'Stage42 live gray human review package written: {md}')
    print(f'Stage42 readonly rehearsal package written: {reh_md}')
    print(f'decision={report.decision}')
    return 1 if report.decision == LiveGrayReviewDecision.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
