#!/usr/bin/env python
"""Run Stage 28 dry-run monitoring checks and write reports."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from qmt_ai_trading.monitoring.service import MonitoringConfig, run_monitoring_check, save_monitoring_json
from qmt_ai_trading.monitoring.formatters import format_monitoring_markdown


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run dry-run monitoring and circuit-breaker checks.")
    p.add_argument("--output", default="monitoring_reports/monitoring.md")
    p.add_argument("--json-output", default="monitoring_reports/monitoring.json")
    p.add_argument("--alert-output-dir", default=None)
    p.add_argument("--quality-level", default="UNKNOWN")
    p.add_argument("--fallback-used", action="store_true")
    p.add_argument("--risk-reject-count", type=int, default=0)
    p.add_argument("--scheduler-exit-code", type=int, default=0)
    p.add_argument("--max-drawdown", type=float, default=0.0)
    p.add_argument("--dry-run-alerts", action="store_true", default=True)
    args = p.parse_args(argv)
    report = run_monitoring_check(MonitoringConfig(args.quality_level, args.fallback_used, args.risk_reject_count, args.scheduler_exit_code, args.max_drawdown, dry_run_alerts=args.dry_run_alerts, alert_output_dir=args.alert_output_dir))
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(format_monitoring_markdown(report), encoding="utf-8")
    save_monitoring_json(report, args.json_output)
    print(format_monitoring_markdown(report))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
