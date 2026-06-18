from __future__ import annotations
from collections import defaultdict
from uuid import uuid4
from .models import DataQualityTrend

def summarize_quality_trend(entries_for_symbol):
    rows=sorted(entries_for_symbol, key=lambda e: e.trade_date); n=len(rows)
    levels=[str(e.quality_level).split('.')[-1].upper() for e in rows]
    avg=sum(float(e.coverage_ratio) for e in rows)/n if n else 0.0
    meta={}
    if n>=2:
        meta["coverage_delta"]=rows[-1].coverage_ratio-rows[0].coverage_ratio; meta["missing_bars_delta"]=rows[-1].missing_bars-rows[0].missing_bars; meta["anomaly_count_delta"]=rows[-1].anomaly_count-rows[0].anomaly_count
    level="FAIL" if "FAIL" in levels or avg<0.5 else "WARN" if any(x in levels for x in ["WARN","UNAVAILABLE"]) or avg<0.8 or meta.get("coverage_delta",0)<-0.1 or meta.get("missing_bars_delta",0)>0 or meta.get("anomaly_count_delta",0)>0 else "PASS" if n else "UNKNOWN"
    return DataQualityTrend(f"dq-trend-{uuid4().hex[:12]}", rows[0].symbol if rows else "", rows[0].trade_date if rows else "", rows[-1].trade_date if rows else "", n, levels.count("PASS"), levels.count("WARN"), levels.count("FAIL"), levels.count("UNKNOWN")+levels.count("SKIPPED"), levels.count("UNAVAILABLE"), avg, max([e.missing_bars for e in rows] or [0]), max([e.anomaly_count for e in rows] or [0]), level, f"{level}: {n} observations, average coverage {avg:.2%}", meta)
def build_quality_trends(entries):
    groups=defaultdict(list)
    for e in entries or []: groups[e.symbol].append(e)
    return [summarize_quality_trend(v) for k,v in sorted(groups.items())]
def classify_quality_trend(trend): return str(trend.trend_level)
def compare_quality_trends(previous,current):
    return {"coverage_delta": current.average_coverage-previous.average_coverage, "missing_bars_delta": current.max_missing_bars-previous.max_missing_bars, "anomaly_count_delta": current.max_anomaly_count-previous.max_anomaly_count}
def format_quality_trend_summary(trends):
    return "\n".join(f"- {t.symbol}: {t.trend_level} avg_coverage={t.average_coverage:.2%}" for t in trends)
