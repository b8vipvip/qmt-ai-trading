from __future__ import annotations
from .real_xtdata_loader import SAFETY

def evaluate_quality(cache, min_bars=20):
    decisions=[]
    for sym,item in cache.get('symbols',{}).items():
        bars=item.get('bars',[]); bad=[b for b in bars if not all(k in b and b[k] is not None for k in ['open','high','low','close','volume'])]
        ok=len(bars)>=min_bars and not bad
        decisions.append({'symbol':sym,'status':'PASS' if ok else 'WARN','bar_count':len(bars),'issues':([] if ok else ['insufficient_bars' if len(bars)<min_bars else 'missing_ohlcv']),'dry_run':True,'read_only':True})
    return {'stage':'Stage88','gate':'Data Quality Gate','status':'PASS' if all(d['status']=='PASS' for d in decisions) else 'WARN','decisions':decisions,**SAFETY}
