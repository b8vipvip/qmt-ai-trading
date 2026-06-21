from __future__ import annotations
from .models import MarketDataQualityReport
def build_quality_report(symbols, snapshots, bars):
    warnings=[]; timestamps=[x.get('timestamp') for x in snapshots+bars]
    missing_ts=sum(1 for t in timestamps if not t); dup=len(timestamps)-len(set(timestamps))
    missing_price=sum(1 for x in snapshots+bars if x.get('close') is None and x.get('last_price') is None)
    zero_volume=sum(1 for x in snapshots+bars if x.get('volume',1)==0)
    outlier=sum(1 for x in snapshots+bars if (x.get('close') or x.get('last_price') or 0)>1000)
    if dup: warnings.append('duplicate timestamps detected in sandbox data')
    q='BAD' if missing_ts or missing_price else ('WARNING' if dup or zero_volume or outlier else 'GOOD')
    return MarketDataQualityReport(len(symbols), len(snapshots), len(bars), 0, missing_ts, dup, 0, missing_price, zero_volume, outlier, q, warnings).to_dict()
