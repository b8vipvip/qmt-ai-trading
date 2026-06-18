from __future__ import annotations
from collections import defaultdict
from qmt_ai_trading.performance.models import FactorAttribution

_FACTORS=("score","momentum","volatility","volume")

def _get_metric(obj, name):
    m=getattr(obj,"metrics", None) or getattr(obj,"metadata", None) or (obj.get("metrics",{}) if isinstance(obj,dict) else {})
    if name in m: return m[name]
    aliases={"momentum":["momentum_score"],"volatility":["volatility_score"],"volume":["volume_factor","volume_score"]}
    for a in aliases.get(name,[]):
        if a in m: return m[a]
    return getattr(obj,name, obj.get(name,0) if isinstance(obj,dict) else 0)

def attribute_by_factor(candidates_by_date, selected_by_date, trades):
    allowed_symbols={getattr(t,"symbol","") for t in trades or [] if getattr(t,"allowed_by_risk",True)}
    result=[]
    for f in _FACTORS:
        vals=[]; wins=0; n=0
        for d, items in (selected_by_date or {}).items():
            for it in items or []:
                try: val=float(_get_metric(it,f) or 0)
                except Exception: val=0.0
                vals.append(val); n+=1
                if getattr(it,"symbol", it.get("symbol","") if isinstance(it,dict) else "") in allowed_symbols: wins+=1
        avg=sum(vals)/len(vals) if vals else 0.0
        result.append(FactorAttribution(f, avg/100.0 if abs(avg)>1 else avg, avg, avg, wins/n if n else 0.0, {"method":"approximate_selected_factor_average"}))
    return result

def attribute_by_symbol(trades, equity_curve):
    data=defaultdict(lambda:{"allowed_count":0,"blocked_count":0,"allowed_value":0.0,"blocked_value":0.0})
    for t in trades or []:
        s=getattr(t,"symbol",""); v=abs(float(getattr(t,"value",0) or 0))
        if getattr(t,"allowed_by_risk",True): data[s]["allowed_count"]+=1; data[s]["allowed_value"]+=v
        else: data[s]["blocked_count"]+=1; data[s]["blocked_value"]+=v
    return dict(data)

def attribute_by_risk_gate(trades):
    blocked=[t for t in trades or [] if not getattr(t,"allowed_by_risk",True)]
    return {"blocked_count":len(blocked),"blocked_value":sum(abs(float(getattr(t,"value",0) or 0)) for t in blocked),"blocked_reasons":dict((getattr(t,"blocked_reason","") or "unknown", sum(1 for x in blocked if (getattr(x,"blocked_reason","") or "unknown")== (getattr(t,"blocked_reason","") or "unknown"))) for t in blocked)}

def format_factor_attribution(items):
    lines=["| Factor | Contribution | Avg Exposure | Avg Score | Win Rate |","| --- | ---: | ---: | ---: | ---: |"]
    for a in items or []:
        lines.append(f"| {a.factor_name} | {a.contribution:.4f} | {a.average_exposure:.4f} | {a.average_score:.4f} | {a.win_rate:.2%} |")
    return "\n".join(lines)
