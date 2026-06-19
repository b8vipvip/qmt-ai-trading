#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.live_env_snapshot.models import LiveEnvSnapshotDecision as D
from qmt_ai_trading.live_env_snapshot.service import build_default_live_env_snapshot_config, run_live_env_snapshot, run_readonly_environment_snapshot, save_live_env_snapshot_report, save_readonly_environment_snapshot_report

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate Stage44 read-only live environment snapshot and config freeze review.')
    p.add_argument('--repo-root', default='.')
    p.add_argument('--output-dir', default='live_env_snapshot_stage44')
    p.add_argument('--signature-freeze-dir', default='live_signature_freeze_stage43')
    p.add_argument('--review-dir', default='live_gray_review_stage42')
    p.add_argument('--ledger-dir', default='live_gray_ledger_stage41')
    p.add_argument('--redline-review-dir', default='redline_review_stage40')
    p.add_argument('--output', default='live_env_snapshot_stage44/live_env_snapshot.md')
    p.add_argument('--json-output', default='live_env_snapshot_stage44/live_env_snapshot.json')
    p.add_argument('--snapshot-output', default='live_env_snapshot_stage44/readonly_environment_snapshot.md')
    p.add_argument('--snapshot-json-output', default='live_env_snapshot_stage44/readonly_environment_snapshot.json')
    a=p.parse_args(argv)
    cfg=build_default_live_env_snapshot_config(a.repo_root, output_dir=a.output_dir, signature_freeze_dir=a.signature_freeze_dir, review_dir=a.review_dir, ledger_dir=a.ledger_dir, redline_review_dir=a.redline_review_dir)
    report=run_live_env_snapshot(cfg); snap=run_readonly_environment_snapshot(report)
    save_live_env_snapshot_report(report, a.output, a.json_output); save_readonly_environment_snapshot_report(snap, a.snapshot_output, a.snapshot_json_output)
    print(f'Stage44 read-only live env snapshot decision={report.decision.value if hasattr(report.decision,"value") else report.decision}')
    print(f'live_env_snapshot={a.output}')
    print(f'readonly_environment_snapshot={a.snapshot_output}')
    return 1 if report.decision == D.NO_GO else 0
if __name__=='__main__': raise SystemExit(main())
