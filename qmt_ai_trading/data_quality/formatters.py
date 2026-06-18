from __future__ import annotations
import json
from .models import SAFETY_NOTE

def format_ledger_entry(e): return f"| {e.symbol} | {e.trade_date} | {e.quality_level} | {e.coverage_ratio:.2%} | {e.loaded_bars} | {e.missing_bars} | {e.duplicate_bars} | {e.anomaly_count} |"
def format_quality_trend(t): return f"| {t.symbol} | {t.start_date} | {t.end_date} | {t.trend_level} | {t.observations} | {t.average_coverage:.2%} | {t.max_missing_bars} | {t.max_anomaly_count} |"
def format_quality_incident(i): return f"- **{i.severity} {i.category} {i.symbol}**: {i.title}. {i.message} Remediation: {i.remediation}"
def format_data_quality_tracking_json(report): return json.dumps(report.to_dict(),ensure_ascii=False,indent=2,sort_keys=True)
def format_data_quality_tracking_markdown(report):
    lines=["# Data quality tracking summary","",f"Source: {report.source or 'none'}",f"Period: {report.start_date or '-'} to {report.end_date or '-'}","","## Ledger summary",f"Total ledger entries: {len(report.ledger_entries)}","","| Symbol | Date | Level | Coverage | Loaded | Missing | Duplicate | Anomaly |","|---|---|---:|---:|---:|---:|---:|---:|"]
    lines += [format_ledger_entry(e) for e in report.ledger_entries[:200]] or ["| - | - | UNKNOWN | 0.00% | 0 | 0 | 0 | 0 |"]
    lines += ["","## Trends","","| Symbol | Start | End | Level | Obs | Avg coverage | Max missing | Max anomaly |","|---|---|---|---:|---:|---:|---:|---:|"]
    lines += [format_quality_trend(t) for t in report.trends] or ["| - | - | - | UNKNOWN | 0 | 0.00% | 0 | 0 |"]
    lines += ["","## Incidents",""] + ([format_quality_incident(i) for i in report.incidents] or ["- No data quality incidents detected."])
    lines += ["","## Remediation","","Review WARNING/ERROR incidents, refill local cache, and rerun the read-only tracker before any later manual stage.","","## Safety note",report.safety_note or SAFETY_NOTE]
    return "\n".join(lines)+"\n"
