#!/usr/bin/env python
"""Build the stage 31 read-only local dashboard as a single HTML file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qmt_ai_trading.dashboard.safety import build_default_dashboard_config
from qmt_ai_trading.dashboard.service import build_and_save_dashboard


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build QMT AI Trading read-only dashboard.")
    parser.add_argument("--output", default="dashboard_stage31/index.html")
    parser.add_argument("--report-dir", default="reports")
    parser.add_argument("--monitoring-dir", default="monitoring_reports")
    parser.add_argument("--agent-dir", default="agent_reports")
    parser.add_argument("--live-gray-dir", default="live_gray_reports")
    parser.add_argument("--approval-dir", default="approvals")
    parser.add_argument("--paper-dir", default="paper_orders")
    parser.add_argument("--cache-quality-dir", default="qmt_data_quality_reports")
    parser.add_argument("--title", default="QMT AI Trading Dashboard")
    args = parser.parse_args(argv)

    config = build_default_dashboard_config(
        output_path=args.output,
        report_dir=args.report_dir,
        monitoring_dir=args.monitoring_dir,
        agent_dir=args.agent_dir,
        live_gray_dir=args.live_gray_dir,
        approval_dir=args.approval_dir,
        paper_dir=args.paper_dir,
        cache_quality_dir=args.cache_quality_dir,
        title=args.title,
    )
    data, path = build_and_save_dashboard(config)
    print(f"Dashboard written: {path}")
    print("Read-only dashboard. No QMT, xttrader, order submission, approval mutation, or external network call was performed.")
    print(f"Sections: {len(data.sections)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
