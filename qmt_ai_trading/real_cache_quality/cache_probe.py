from __future__ import annotations
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from qmt_ai_trading.datahub.local_store import LocalBarStore, BarQuery
from qmt_ai_trading.datahub.models import MarketBar
from .models import *

def _ev(cat, st, sev, title, summary, path='', meta=None): return RealCacheQualityEvidence(cat,st,sev,title,summary,path,meta or {})
def _read_rows(path: Path):
    rows=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip():
            try: rows.append(json.loads(line))
            except Exception: rows.append({"_bad_json": line})
    return rows
def probe_cache_root(root: Path):
    if not root.exists(): return _ev(RealCacheQualityCategory.CACHE_COVERAGE,RealCacheQualityStatus.UNAVAILABLE,RealCacheQualitySeverity.WARN,"cache root",f"cache root missing: {root}",str(root))
    return _ev(RealCacheQualityCategory.CACHE_COVERAGE,RealCacheQualityStatus.PASS,RealCacheQualitySeverity.INFO,"cache root",f"cache root readable: {root}",str(root))
def probe_symbol_bar_files(root: Path, max_symbols:int=5): return sorted(root.glob(f"*/*/*.bars.jsonl"))[:max(1,min(max_symbols,5))] if root.exists() else []
def probe_cache_coverage(root: Path, max_symbols:int=5):
    items=[]
    for p in probe_symbol_bar_files(root,max_symbols):
        rows=_read_rows(p); dates=sorted({str(r.get('datetime') or r.get('date') or r.get('time') or '')[:10] for r in rows if r})
        sym=p.name.split('.')[0]
        items.append(CacheCoverageItem(sym,len(rows),dates[0] if dates else '',dates[-1] if dates else '',RealCacheQualityStatus.PASS if rows else RealCacheQualityStatus.UNAVAILABLE,f"{len(rows)} bars"))
    return items
def probe_long_sample_completeness(root:Path, min_days:int=40, max_symbols:int=5):
    out=[]
    for c in probe_cache_coverage(root,max_symbols):
        st=RealCacheQualityStatus.PASS if c.bar_count>=min_days else RealCacheQualityStatus.WARN
        out.append(LongSampleCompletenessItem(c.symbol,min_days,c.bar_count,[],st,f"actual_days={c.bar_count}, required_days={min_days}"))
    return out
def probe_field_quality(root:Path, max_symbols:int=5):
    items=[]; required=['open','high','low','close']
    for p in probe_symbol_bar_files(root,max_symbols):
        sym=p.name.split('.')[0]; rows=_read_rows(p); dates=[]; dup=0; missing=0; ohlc=0; vol=0; timebad=0
        for r in rows:
            d=str(r.get('datetime') or r.get('date') or r.get('time') or '')[:10];
            if not d or len(d)<8: timebad+=1
            dates.append(d)
            if any(r.get(k) in (None,'') for k in required): missing+=1; continue
            try:
                o,h,l,c=[float(r[k]) for k in required]
                if min(o,h,l,c)<0 or h<max(o,c) or l>min(o,c): ohlc+=1
                if r.get('volume') not in (None,'') and float(r.get('volume'))<0: vol+=1
                if r.get('amount') not in (None,'') and float(r.get('amount'))<0: vol+=1
            except Exception: ohlc+=1
        dup=len(dates)-len(set(dates))
        def add(field, count, cat): items.append(FieldQualityItem(sym,field,RealCacheQualityStatus.PASS if count==0 else RealCacheQualityStatus.FAIL,count,f"{field} issue_count={count}"))
        add('date/time',timebad,RealCacheQualityCategory.TRADING_DAY_TIME); add('missing_ohlc',missing,RealCacheQualityCategory.MISSING_VALUE); add('duplicate_date',dup,RealCacheQualityCategory.DUPLICATE_BAR); add('ohlc_logic',ohlc,RealCacheQualityCategory.OHLC_VALIDITY); add('volume_amount',vol,RealCacheQualityCategory.VOLUME_AMOUNT_VALIDITY)
    return items
def probe_missing_duplicate_bars(root:Path,max_symbols:int=5): return [x for x in probe_field_quality(root,max_symbols) if x.field in {'missing_ohlc','duplicate_date'}]
def probe_cache_roundtrip_with_mock_provider(root:Path):
    store=LocalBarStore(root); today=date(2026,6,18); bars=[MarketBar(symbol='510300.SH', datetime=(today-timedelta(days=i)).isoformat(), open=1+i, high=1.1+i, low=.9+i, close=1.05+i, volume=1000+i, amount=10000+i, source='mock') for i in range(3)]
    store.save_bars('510300.SH','1d',bars,provider='mock_stage56')
    got=store.load_bars(BarQuery(['510300.SH'],(today-timedelta(days=2)).isoformat(),today.isoformat(),'1d'))
    return _ev(RealCacheQualityCategory.CACHE_COVERAGE,RealCacheQualityStatus.PASS if len(got)>=3 else RealCacheQualityStatus.FAIL,RealCacheQualitySeverity.INFO if len(got)>=3 else RealCacheQualitySeverity.CRITICAL,'mock cache roundtrip',f'roundtrip bars={len(got)}',str(root),{'bars':len(got)})
