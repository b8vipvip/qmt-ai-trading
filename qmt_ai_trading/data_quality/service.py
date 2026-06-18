from __future__ import annotations
import json
from pathlib import Path
from uuid import uuid4
from .models import DataQualityTrackingReport, SAFETY_NOTE
from .ledger import load_quality_reports_from_dir, build_ledger_entries_from_quality_reports, build_ledger_entries_from_cache_scan, merge_ledger_entries
from .trend import build_quality_trends
from .incidents import *
from .formatters import format_data_quality_tracking_markdown, format_data_quality_tracking_json
from .safety import sanitize_data_quality_metadata, validate_data_quality_tracking_is_read_only, validate_no_trading_side_effect

def _assemble(entries, source, start_date="", end_date="", min_coverage=0.8, metadata=None):
    entries=merge_ledger_entries(entries); trends=build_quality_trends(entries)
    incidents=deduplicate_quality_incidents(detect_coverage_incidents(entries,min_coverage)+detect_missing_bar_incidents(entries)+detect_duplicate_bar_incidents(entries)+detect_anomaly_incidents(entries)+detect_unavailable_incidents(entries))
    summary={"ledger_entries":len(entries),"trends":len(trends),"incidents":len(incidents),"error_incidents":sum(1 for i in incidents if i.severity in {"ERROR","CRITICAL"})}
    r=DataQualityTrackingReport(f"dq-tracking-{uuid4().hex[:12]}", source=source, start_date=start_date, end_date=end_date, ledger_entries=entries, trends=trends, incidents=incidents, summary=summary, success=True, message="data quality tracking completed" if entries else "empty data quality tracking report", safety_note=SAFETY_NOTE, metadata=sanitize_data_quality_metadata(metadata or {}))
    validate_no_trading_side_effect(r); return r
def run_data_quality_tracking_from_reports(report_dir, *, start_date="", end_date="", min_coverage=0.8, metadata=None):
    validate_data_quality_tracking_is_read_only(); return _assemble(build_ledger_entries_from_quality_reports(load_quality_reports_from_dir(report_dir)), f"reports:{report_dir}", start_date,end_date,min_coverage,metadata)
def run_data_quality_tracking_from_cache(cache_root, symbols, start_date, end_date, frequency="1d", min_coverage=0.8, metadata=None):
    validate_data_quality_tracking_is_read_only(); return _assemble(build_ledger_entries_from_cache_scan(cache_root,symbols,start_date,end_date,frequency), f"cache:{cache_root}", start_date,end_date,min_coverage,metadata)
def run_data_quality_tracking(report_dir=None, cache_root=None, symbols=None, start_date="", end_date="", frequency="1d", min_coverage=0.8, metadata=None):
    validate_data_quality_tracking_is_read_only(); entries=[]; sources=[]
    if report_dir: entries += build_ledger_entries_from_quality_reports(load_quality_reports_from_dir(report_dir)); sources.append(f"reports:{report_dir}")
    if cache_root and symbols: entries += build_ledger_entries_from_cache_scan(cache_root, symbols, start_date, end_date, frequency); sources.append(f"cache:{cache_root}")
    return _assemble(entries, ", ".join(sources) if sources else "empty", start_date,end_date,min_coverage,metadata)
def save_data_quality_tracking_report(report, output_path):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True)
    text=format_data_quality_tracking_json(report) if p.suffix.lower()==".json" else format_data_quality_tracking_markdown(report)
    p.write_text(text,encoding="utf-8"); return p
def load_data_quality_tracking_report(path):
    data=json.loads(Path(path).read_text(encoding="utf-8")); return DataQualityTrackingReport(**data)
