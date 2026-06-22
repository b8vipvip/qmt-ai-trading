from __future__ import annotations
from .paper_broker import is_allowed
from .models import RiskReplayResult
def replay(orders):
    res=[]
    for o in orders:
        allowed=is_allowed(o.risk_decision); violation=(not allowed and o.fill_status=="FILLED")
        reasons=o.risk_decision.get("reasons") or o.risk_decision.get("reject_reasons") or (["Risk Gate allowed"] if allowed else [o.reject_reason or "Risk Gate rejected"])
        res.append(RiskReplayResult(o.order_id,allowed,list(reasons),violation))
    return res
