#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.notification_dryrun.service import run_notification_dry_run_from_files
from qmt_ai_trading.notification_dryrun.formatters import format_notification_dry_run_markdown

def main(argv=None):
    p=argparse.ArgumentParser(description='Generate local notification dry-run previews only.')
    for a in ['daily-report','monitoring-report','data-quality-report','agent-memo','live-gray-report','final-acceptance']:
        p.add_argument('--'+a, default=None)
    p.add_argument('--channels', default='FILE,CONSOLE'); p.add_argument('--recipients', default='')
    p.add_argument('--output', default='notification_dryrun/notification_dryrun.md'); p.add_argument('--json-output', default=None)
    p.add_argument('--preview-output-dir', default=None); p.add_argument('--strict', action='store_true')
    a=p.parse_args(argv)
    report=run_notification_dry_run_from_files(daily_report=a.daily_report, monitoring_report=a.monitoring_report, data_quality_report=a.data_quality_report, agent_memo=a.agent_memo, live_gray_report=a.live_gray_report, final_acceptance=a.final_acceptance, channels=a.channels, recipients=a.recipients, output_path=a.output, json_output_path=a.json_output, preview_output_dir=a.preview_output_dir)
    print(format_notification_dry_run_markdown(report))
    return 1 if a.strict and not report.audit_result.passed else 0
if __name__=='__main__': raise SystemExit(main())
