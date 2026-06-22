from __future__ import annotations
from .models import ShadowPnL
def compute_pnl(portfolio, initial_cash=100000.0):
    unreal=sum(p.get("unrealized_pnl",0.0) for p in portfolio.positions); daily=portfolio.paper_total_value-initial_cash; ret=daily/initial_cash if initial_cash else 0.0; dd=max(0.0,-ret)
    warnings=[]
    if portfolio.paper_position_value > portfolio.paper_total_value*0.8: warnings.append("虚拟仓位超过 80% 上限")
    return ShadowPnL(unreal,0.0,daily,ret,dd,warnings)
