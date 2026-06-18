#!/usr/bin/env python
from __future__ import annotations
import argparse, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from qmt_ai_trading.data_quality.service import run_data_quality_tracking, save_data_quality_tracking_report
from qmt_ai_trading.data_quality.formatters import format_data_quality_tracking_markdown

def main(argv=None):
    p=argparse.ArgumentParser(description="Run read-only QMT data quality tracking.")
    p.add_argument("--report-dir"); p.add_argument("--cache-root"); p.add_argument("--symbols",default=""); p.add_argument("--start",default=""); p.add_argument("--end",default=""); p.add_argument("--frequency",default="1d"); p.add_argument("--min-coverage",type=float,default=0.8); p.add_argument("--output"); p.add_argument("--json-output"); p.add_argument("--strict",action="store_true")
    a=p.parse_args(argv); syms=[x.strip() for x in a.symbols.split(',') if x.strip()]
    report=run_data_quality_tracking(a.report_dir,a.cache_root,syms,a.start,a.end,a.frequency,a.min_coverage,metadata={"cli":"run_data_quality_tracking"})
    if a.output: save_data_quality_tracking_report(report,a.output)
    if a.json_output: save_data_quality_tracking_report(report,a.json_output)
    print(format_data_quality_tracking_markdown(report))
    bad=any(i.severity in {"ERROR","CRITICAL"} for i in report.incidents) or any(str(t.trend_level)=="FAIL" for t in report.trends)
    return 2 if a.strict and bad else 0
if __name__=="__main__": raise SystemExit(main())
