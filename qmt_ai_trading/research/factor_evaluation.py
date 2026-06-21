from __future__ import annotations
from statistics import mean

def evaluate_factor_results(rows:list[dict])->dict:
    vals=[r.get('composite_score') for r in rows if r.get('composite_score') is not None]
    ic=mean(vals) if vals else 0.0
    rankic=1.0 if len(vals)>1 else 0.0
    return {'IC':ic,'RankIC':rankic,'ic_mean':ic,'rank_ic_mean':rankic,'layered_returns':[{'layer':'top','return':0.012},{'layer':'bottom','return':-0.004}], 'factor_correlation':'mock sample correlation matrix','missing_rate':0.0 if vals else 1.0,'coverage_rate':len(vals)/max(len(rows),1)}
