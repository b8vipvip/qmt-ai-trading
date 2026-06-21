from __future__ import annotations
from datetime import datetime, timedelta
from math import sqrt
from statistics import mean, pstdev
from typing import Any
from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.datahub.models import MarketBar
from .factor_config import build_default_config

def make_mock_bars(symbol:str, days:int=90)->list[MarketBar]:
    base=2.5+(abs(hash(symbol))%120)/100; bars=[]
    for i in range(days):
        close=base*(1+0.0015*i+0.015*((i%11)-5)/100); volume=1000000+(i%17)*25000+(abs(hash(symbol))%1000)
        bars.append(MarketBar(symbol, (datetime.utcnow()-timedelta(days=days-i)).date().isoformat(), close*0.99, close*1.01, close*0.98, close, volume, source='mock'))
    return bars

def _closes(bars): return [float(b.close) for b in bars if b.close and b.close>0]
def _vols(bars): return [float(b.volume) for b in bars if b.volume is not None]
def _ret(closes, w): return (closes[-1]/closes[-w-1]-1) if len(closes)>=w+1 else None

def compute_factor_value(factor_id:str,bars:list[MarketBar],params:dict[str,Any]|None=None)->float|None:
    params=params or {}; c=_closes(bars); v=_vols(bars)
    if factor_id.startswith('momentum_'): return _ret(c,int(params.get('window',factor_id.split('_')[1][:-1])))
    if factor_id=='return_reversal_5d':
        x=_ret(c,int(params.get('window',5))); return -x if x is not None else None
    if factor_id=='volatility_20d':
        w=int(params.get('window',20));
        if len(c)<w+1: return None
        rs=[c[i]/c[i-1]-1 for i in range(len(c)-w, len(c)) if c[i-1]>0]
        return pstdev(rs)*sqrt(252) if len(rs)>1 else None
    if factor_id=='volume_ratio_20d':
        w=int(params.get('window',20)); return (v[-1]/mean(v[-w:])) if len(v)>=w and mean(v[-w:]) else None
    if factor_id=='drawdown_60d':
        w=int(params.get('window',60)); s=c[-w:] if len(c)>=w else []
        return min((x/max(s[:i+1])-1 for i,x in enumerate(s)), default=None) if s else None
    if factor_id=='ma_trend_20_60':
        sw=int(params.get('short_window',20)); lw=int(params.get('long_window',60))
        return mean(c[-sw:])/mean(c[-lw:])-1 if len(c)>=lw else None
    return None

def run_factor_scan(params:dict[str,Any]|None=None)->dict[str,Any]:
    params=params or {}; factor_set=params.get('factor_set') or [c.factor_id for c in build_default_config() if c.enabled]
    cfg={c.factor_id:c for c in build_default_config()}; rows=[]
    for item in get_default_etf_universe():
        bars=make_mock_bars(item.symbol, 90); vals={fid:compute_factor_value(fid,bars,(cfg.get(fid).params if cfg.get(fid) else {})) for fid in factor_set}
        nums=[(v, cfg[f].weight, -1 if cfg[f].direction=='negative' else 1) for f,v in vals.items() if v is not None and f in cfg]
        score=sum(v*w*d for v,w,d in nums)/sum(abs(w) for _,w,_ in nums) if nums else None
        rows.append({'symbol':item.symbol,'factor_values':vals,'composite_score':score,'rank':0,'reasons':[f'{k}={v:.4f}' for k,v in vals.items() if v is not None][:3],'risk_flags':['not_live_trading','mock_data']})
    rows=sorted(rows,key=lambda r:(r['composite_score'] is not None, r['composite_score'] or -999), reverse=True)
    for i,r in enumerate(rows,1): r['rank']=i
    from .factor_evaluation import evaluate_factor_results
    from .candidate_builder import build_candidates
    from .factor_report import build_factor_report
    evaluation=evaluate_factor_results(rows); candidates=build_candidates(rows); report=build_factor_report(rows,evaluation,candidates,params)
    return {'ok':True,'task_id':'factor_scan','data_source':'mock','quality_level':'sample_offline','not_live_trading':True,'factor_results':rows,'factor_evaluation':evaluation,'factor_candidates':candidates,'factor_report':report,'artifacts':['factor_results.json','factor_evaluation.json','factor_candidates.json','factor_report.json']}
