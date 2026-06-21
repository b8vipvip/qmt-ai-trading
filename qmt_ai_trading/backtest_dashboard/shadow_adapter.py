from __future__ import annotations
from .safety import with_safety

def run_shadow_replay(context):
    rows=[]
    for i,s in enumerate(context.get('linked_symbols',[]) or ['510300.SH']):
        ret=round(0.012+i*0.007,4); dd=round(0.025+i*0.006,4)
        rows.append({'symbol':s,'shadow_trade_id':f'shadow-{i+1}','signal':'WATCH_ONLY','mock_return':ret,'max_drawdown':dd,'win':ret>0,'holding_days':5+i,'linked_trade_intent':f'mock-intent-{i+1}','dry_run':True,'not_live_trading':True,'research_only':True})
    return with_safety({'stage':'Stage82','backtest_mode':'mock_shadow','shadow_replay':rows,'trade_count':len(rows),'data_quality':context.get('data_quality','fallback_safe')})
