#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_signature_freeze.models import LiveSignatureFreezeDecision as D
from qmt_ai_trading.live_signature_freeze.service import build_default_live_signature_freeze_config, run_config_freeze_summary, run_live_signature_freeze, save_config_freeze_report, save_live_signature_freeze_report

def main(argv=None)->int:
    p=argparse.ArgumentParser(description='Generate Stage43 read-only signature checklist and config freeze summary.')
    p.add_argument('--repo-root', default='.')
    p.add_argument('--output-dir', default='live_signature_freeze_stage43')
    p.add_argument('--review-dir', default='live_gray_review_stage42')
    p.add_argument('--ledger-dir', default='live_gray_ledger_stage41')
    p.add_argument('--redline-review-dir', default='redline_review_stage40')
    p.add_argument('--output', default='live_signature_freeze_stage43/live_signature_freeze.md')
    p.add_argument('--json-output', default='live_signature_freeze_stage43/live_signature_freeze.json')
    p.add_argument('--config-freeze-output', default='live_signature_freeze_stage43/config_freeze.md')
    p.add_argument('--config-freeze-json-output', default='live_signature_freeze_stage43/config_freeze.json')
    a=p.parse_args(argv)
    cfg=build_default_live_signature_freeze_config(a.repo_root, output_dir=a.output_dir, review_dir=a.review_dir, ledger_dir=a.ledger_dir, redline_review_dir=a.redline_review_dir)
    report=run_live_signature_freeze(cfg); freeze=run_config_freeze_summary(report)
    save_live_signature_freeze_report(report, a.output, a.json_output); save_config_freeze_report(freeze, a.config_freeze_output, a.config_freeze_json_output)
    print(f'Stage43 signature checklist written: {a.output}')
    print(f'Stage43 config freeze summary written: {a.config_freeze_output}')
    print(f'Decision: {report.decision}')
    return 1 if report.decision==D.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
