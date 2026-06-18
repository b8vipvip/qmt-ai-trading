from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable
from qmt_ai_trading.datahub.symbols import normalize_symbol
from .models import PortfolioTarget, PortfolioWeightMethod

@dataclass
class PortfolioAllocationConfig:
    method: str = PortfolioWeightMethod.SCORE_WEIGHT.value
    top_n: int = 2
    cash_reserve_ratio: float = 0.2
    max_symbol_weight: float = 0.3
    max_portfolio_weight: float = 0.8
    min_score: float | None = None
    use_volatility_penalty: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

def _score(c):
    v=getattr(c,'score',0.0); return float(v or 0.0)
def _vol(c):
    m=dict(getattr(c,'metrics',{}) or getattr(c,'metadata',{}) or {})
    return float(m.get('volatility') or m.get('volatility_score') or 0.0)
def _eligible(c,cfg): return bool(getattr(c,'eligible',True)) and (cfg.min_score is None or _score(c)>=cfg.min_score)
def _base(c,w,reason): return PortfolioTarget(normalize_symbol(str(getattr(c,'symbol',''))), w, 0.0, _score(c), reason, dict(getattr(c,'metrics',{}) or {}))
def _selected(candidates,cfg):
    xs=[c for c in candidates if _eligible(c,cfg) and str(getattr(c,'symbol','')).strip()]
    xs.sort(key=_score, reverse=True); return xs[:max(0,int(cfg.top_n or 0))]

def cap_symbol_weights(targets, max_symbol_weight):
    cap=float(max_symbol_weight); 
    for t in targets: t.target_weight=min(max(0.0,float(t.target_weight)),cap)
    return targets

def normalize_target_weights(targets, max_portfolio_weight, cash_reserve_ratio):
    limit=min(float(max_portfolio_weight), max(0.0, 1.0-float(cash_reserve_ratio)))
    total=sum(max(0.0,t.target_weight) for t in targets)
    if total>0 and total>limit:
        ratio=limit/total
        for t in targets: t.target_weight*=ratio
    return targets

def allocate_equal_weight(candidates, config):
    xs=_selected(list(candidates or []), config)
    if not xs: return []
    return [_base(c,1.0/len(xs),'equal_weight allocation') for c in xs]

def allocate_score_weight(candidates, config):
    xs=_selected(list(candidates or []), config)
    if not xs: return []
    scores=[max(0.0,_score(c)) for c in xs]; total=sum(scores) or len(xs)
    return [_base(c,(scores[i]/total if sum(scores)>0 else 1/len(xs)),'score_weight allocation') for i,c in enumerate(xs)]

def allocate_risk_adjusted_weight(candidates, config):
    xs=_selected(list(candidates or []), config)
    if not xs: return []
    vals=[]
    for c in xs:
        penalty=(1.0+_vol(c)) if config.use_volatility_penalty else 1.0
        vals.append(max(0.0,_score(c))/penalty)
    total=sum(vals) or len(xs)
    return [_base(c,(vals[i]/total if sum(vals)>0 else 1/len(xs)),'risk_adjusted_weight allocation') for i,c in enumerate(xs)]

def build_portfolio_targets(candidates, method=None, config=None):
    cfg=config or PortfolioAllocationConfig(method=method or PortfolioWeightMethod.SCORE_WEIGHT.value)
    m=(method or cfg.method or '').value if hasattr(method or cfg.method,'value') else str(method or cfg.method)
    if m==PortfolioWeightMethod.EQUAL_WEIGHT.value: targets=allocate_equal_weight(candidates,cfg)
    elif m==PortfolioWeightMethod.RISK_ADJUSTED_WEIGHT.value: targets=allocate_risk_adjusted_weight(candidates,cfg)
    else: targets=allocate_score_weight(candidates,cfg)
    targets=cap_symbol_weights(targets,cfg.max_symbol_weight)
    targets=normalize_target_weights(targets,cfg.max_portfolio_weight,cfg.cash_reserve_ratio)
    return targets, ([] if targets else ['no eligible portfolio candidates'])
