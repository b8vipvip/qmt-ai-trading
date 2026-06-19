#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.redline_review.safety import build_default_redline_review_config
from qmt_ai_trading.redline_review.service import run_redline_review, save_redline_review_report
from qmt_ai_trading.redline_review.models import RedlineReviewDecision

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate review-only live switch isolation / red-line review report. No QMT, xttrader, orders, or real notifications.')
    p.add_argument('--repo-root', default='.')
    p.add_argument('--include-path', action='append', default=[]); p.add_argument('--exclude-path', action='append', default=[])
    p.add_argument('--scheduler-preview-file'); p.add_argument('--dashboard-path'); p.add_argument('--operator-name', default=''); p.add_argument('--reviewer-name', default='')
    p.add_argument('--output'); p.add_argument('--json-output'); p.add_argument('--strict', action='store_true')
    a=p.parse_args(argv)
    cfg=build_default_redline_review_config(a.repo_root, include_paths=a.include_path or None, exclude_paths=None, operator_name=a.operator_name, reviewer_name=a.reviewer_name)
    if a.exclude_path: cfg.exclude_paths.extend(a.exclude_path)
    sched=Path(a.scheduler_preview_file).read_text(encoding='utf-8', errors='replace') if a.scheduler_preview_file and Path(a.scheduler_preview_file).exists() else None
    report=run_redline_review(config=cfg, scheduler_preview_text=sched, dashboard_path_or_text=a.dashboard_path)
    if a.output: save_redline_review_report(report,a.output)
    if a.json_output: save_redline_review_report(report,a.json_output)
    print(f"Red-line Review: decision={getattr(report.decision,'value',report.decision)} findings={len(report.findings)} review_only=True")
    return 2 if a.strict and report.decision==RedlineReviewDecision.BLOCKED else 0
if __name__=='__main__': raise SystemExit(main())
