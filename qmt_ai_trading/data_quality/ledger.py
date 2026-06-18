from __future__ import annotations
import json
from pathlib import Path
from uuid import uuid4
from typing import Any, Iterable
from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from .models import DataQualityLedgerEntry, DataQualityLevel
from .safety import sanitize_data_quality_metadata, validate_data_quality_tracking_is_read_only

def _level(v: Any)->str:
    s=str(v or "UNKNOWN").upper(); return "PASS" if s in {"PASS","HIGH","OK"} else "WARN" if s in {"WARN","WARNING","MEDIUM","LOW"} else "FAIL" if s in {"FAIL","ERROR","CRITICAL"} else s if s in {"UNKNOWN","UNAVAILABLE","SKIPPED"} else "UNKNOWN"
def load_quality_report_file(path):
    p=Path(path)
    if not p.exists(): return {"warning": f"quality report file not found: {p}", "path": str(p)}
    try:
        data=json.loads(p.read_text(encoding="utf-8")); data["_source_report_path"]=str(p); return data
    except Exception as exc: return {"warning": repr(exc), "path": str(p)}
def load_quality_reports_from_dir(report_dir, patterns=None):
    root=Path(report_dir)
    if not root.exists(): return []
    pats=patterns or ["*.json","*.qmt_quality.json"]
    out=[]
    for pat in pats:
        for p in root.glob(pat):
            if p.is_file(): out.append(load_quality_report_file(p))
    return out
def _entry_from_row(row: dict[str,Any], default_path=""):
    symbol=str(row.get("symbol") or row.get("code") or "")
    start=str(row.get("trade_date") or row.get("date") or row.get("end_date") or row.get("last_datetime") or "")[:10]
    loaded=int(row.get("loaded_bars") or row.get("normalized_bar_count") or row.get("raw_row_count") or row.get("row_count") or 0)
    expected=int(row.get("expected_bars") or row.get("min_bars") or loaded or 0)
    missing=int(row.get("missing_bars") or max(expected-loaded,0))
    dup=int(row.get("duplicate_bars") or row.get("duplicate_datetime_count") or 0)
    anom=int(row.get("anomaly_count") or row.get("zero_volume_count") or 0)
    field=int(row.get("field_missing_count") or row.get("missing_ohlc_count") or 0)
    cov=float(row.get("coverage_ratio") if row.get("coverage_ratio") is not None else (loaded/expected if expected else (1.0 if loaded else 0.0)))
    lvl=_level(row.get("quality_level") or row.get("decision") or ("PASS" if cov>=0.8 and not missing and not dup and not field else "WARN"))
    return DataQualityLedgerEntry(f"dq-ledger-{uuid4().hex[:12]}", source=str(row.get("provider") or row.get("source") or "qmt_quality_report"), symbol=symbol, trade_date=start, quality_level=lvl, coverage_ratio=cov, loaded_bars=loaded, expected_bars=expected, missing_bars=missing, duplicate_bars=dup, anomaly_count=anom, field_missing_count=field, source_report_path=str(row.get("_source_report_path") or default_path), metadata=sanitize_data_quality_metadata(row.get("metadata",{})))
def build_ledger_entries_from_quality_reports(reports):
    entries=[]
    for report in reports or []:
        rows=report.get("reports") or report.get("symbols") or report.get("entries") or report.get("quality_reports")
        if isinstance(rows, dict): rows=list(rows.values())
        if isinstance(rows, list):
            for r in rows:
                if isinstance(r, dict): entries.append(_entry_from_row({**report, **r}, report.get("_source_report_path","")))
        elif isinstance(report, dict) and (report.get("symbol") or report.get("decision") or report.get("normalized_bar_count") is not None): entries.append(_entry_from_row(report, report.get("_source_report_path","")))
    return entries
def build_ledger_entries_from_cache_scan(cache_root, symbols, start_date, end_date, frequency="1d"):
    validate_data_quality_tracking_is_read_only(); store=LocalBarStore(cache_root); out=[]
    for sym in symbols or []:
        bars=store.load_bars(BarQuery([sym], start_date, end_date, frequency)); dates=[str(getattr(b,"datetime",""))[:10] for b in bars]
        dup=len(dates)-len(set(dates)); loaded=len(bars); expected=max(loaded,1) if loaded else 0; missing=0 if loaded else 1
        out.append(DataQualityLedgerEntry(f"dq-cache-{uuid4().hex[:12]}", source="local_cache_scan", symbol=sym, trade_date=str(end_date), quality_level=("PASS" if loaded and not dup else "UNAVAILABLE" if not loaded else "WARN"), coverage_ratio=(1.0 if loaded else 0.0), loaded_bars=loaded, expected_bars=expected, missing_bars=missing, duplicate_bars=dup, anomaly_count=sum(1 for b in bars if (getattr(b,"close",None) in (None,0) or getattr(b,"volume",None) in (None,0))), field_missing_count=sum(1 for b in bars if None in (getattr(b,"open",None),getattr(b,"high",None),getattr(b,"low",None),getattr(b,"close",None))), metadata={"cache_root": str(cache_root), "frequency": frequency}))
    return out
def merge_ledger_entries(entries):
    seen={}
    for e in entries or []: seen[(e.symbol,e.trade_date,e.source_report_path,e.source)] = e
    return list(seen.values())
def save_ledger_entries(entries, output_path):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps([e.to_dict() for e in entries],ensure_ascii=False,indent=2),encoding="utf-8"); return p
def load_ledger_entries(path):
    p=Path(path)
    if not p.exists(): return []
    return [DataQualityLedgerEntry(**x) for x in json.loads(p.read_text(encoding="utf-8"))]
