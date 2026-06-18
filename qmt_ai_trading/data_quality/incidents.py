from __future__ import annotations
from uuid import uuid4
from .models import DataQualityIncident

def _inc(e,cat,sev,title,msg,rem): return DataQualityIncident(f"dq-incident-{uuid4().hex[:12]}", symbol=e.symbol, category=cat, severity=sev, title=title, message=msg, first_seen=e.trade_date, last_seen=e.trade_date, evidence=[e.to_dict()], remediation=rem)
def detect_coverage_incidents(entries, min_coverage=0.8): return [_inc(e,"coverage","ERROR" if e.coverage_ratio<min_coverage*0.5 else "WARNING","Low data coverage",f"{e.symbol} coverage {e.coverage_ratio:.2%} below {min_coverage:.2%}","Review QMT historical report and refill local cache.") for e in entries if e.coverage_ratio < min_coverage]
def detect_missing_bar_incidents(entries, max_missing_bars=0): return [_inc(e,"missing_bars","WARNING","Missing bars detected",f"{e.symbol} missing bars {e.missing_bars} > {max_missing_bars}","Run cache warmup or inspect source quality report.") for e in entries if e.missing_bars>max_missing_bars]
def detect_duplicate_bar_incidents(entries): return [_inc(e,"duplicate_bars","WARNING","Duplicate bars detected",f"{e.symbol} duplicate bars {e.duplicate_bars}","Deduplicate local cache after manual review.") for e in entries if e.duplicate_bars>0]
def detect_anomaly_incidents(entries): return [_inc(e,"anomaly","ERROR" if e.anomaly_count>=5 else "WARNING","Data anomaly detected",f"{e.symbol} anomaly count {e.anomaly_count}","Inspect prices/volume and upstream QMT historical data.") for e in entries if e.anomaly_count>0]
def detect_unavailable_incidents(entries): return [_inc(e,"unavailable","WARNING","Data unavailable",f"{e.symbol} data quality is unavailable/skipped", "Check QMT xtdata environment or use cached/mock fixtures.") for e in entries if str(e.quality_level).split('.')[-1].upper() in {"UNAVAILABLE","SKIPPED"}]
def deduplicate_quality_incidents(incidents):
    seen={}
    for i in incidents or []: seen[(i.symbol,i.category,i.first_seen,i.title)] = i
    return list(seen.values())
