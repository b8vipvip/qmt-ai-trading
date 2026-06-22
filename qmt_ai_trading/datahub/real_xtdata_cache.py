from __future__ import annotations
from collections import defaultdict
from .real_xtdata_loader import SAFETY

def build_real_cache(bars, context):
    by=defaultdict(list)
    for b in bars: by[b['symbol']].append(b)
    symbols={s: {'symbol':s,'bar_count':len(v),'latest_bar':v[-1] if v else None,'bars':v} for s,v in by.items()}
    return {'stage':'Stage88','cache_type':'datahub_real_xtdata_cache','source':'Data Hub normalized cache','symbols':symbols,'symbol_count':len(symbols),'bar_count':len(bars),**SAFETY, **{k:context.get(k) for k in ['fallback_used','mock_data','real_market_data','sandbox_fallback','xtdata_imported','mini_qmt_connected']}}
