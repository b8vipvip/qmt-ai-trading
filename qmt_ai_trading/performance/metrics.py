"""Dependency-light performance metrics. Max drawdown is returned as a non-positive ratio."""
from __future__ import annotations
import math
from typing import Any
from qmt_ai_trading.performance.models import PortfolioEquityPoint, PortfolioPerformanceSummary


def _equity(p: Any) -> float:
    return float(getattr(p, "equity", p.get("equity", 0.0) if isinstance(p, dict) else 0.0) or 0.0)

def calculate_returns(equity_curve):
    values=[_equity(p) for p in (equity_curve or [])]
    out=[]
    for a,b in zip(values, values[1:]):
        out.append((b/a-1.0) if a else 0.0)
    return out

def calculate_max_drawdown(equity_curve):
    peak=0.0; max_dd=0.0
    for p in equity_curve or []:
        e=_equity(p); peak=max(peak,e)
        dd=(e/peak-1.0) if peak else 0.0
        max_dd=min(max_dd,dd)
    return round(max_dd, 12)

def calculate_volatility(returns, periods_per_year=252):
    r=[float(x) for x in (returns or [])]
    if len(r)<2: return 0.0
    mean=sum(r)/len(r); var=sum((x-mean)**2 for x in r)/(len(r)-1)
    return math.sqrt(var)*math.sqrt(periods_per_year)

def calculate_sharpe(returns, risk_free_rate=0.0, periods_per_year=252):
    r=[float(x) for x in (returns or [])]
    if not r: return 0.0
    per_rf=float(risk_free_rate)/float(periods_per_year or 252)
    excess=[x-per_rf for x in r]
    vol=calculate_volatility(excess, periods_per_year)
    if vol==0: return 0.0
    return (sum(excess)/len(excess))*float(periods_per_year)/vol

def calculate_win_rate(returns):
    r=[float(x) for x in (returns or [])]
    return (sum(1 for x in r if x>0)/len(r)) if r else 0.0

def calculate_turnover(trades, initial_cash):
    if not initial_cash: return 0.0
    return sum(abs(float(getattr(t,"value", t.get("value",0) if isinstance(t,dict) else 0) or 0)) for t in (trades or []) if bool(getattr(t,"allowed_by_risk", t.get("allowed_by_risk", True) if isinstance(t,dict) else True)))/float(initial_cash)

def summarize_performance(equity_curve, trades, initial_cash, start_date='', end_date='', rebalance_count=0, risk_blocked_count=0):
    returns=calculate_returns(equity_curve)
    final=_equity(equity_curve[-1]) if equity_curve else float(initial_cash or 0)
    total=(final/float(initial_cash)-1.0) if initial_cash else 0.0
    years=max(len(returns),1)/252.0
    ann=(1+total)**(1/years)-1 if total>-1 and years>0 else 0.0
    allowed=[t for t in (trades or []) if bool(getattr(t,"allowed_by_risk", True))]
    return PortfolioPerformanceSummary(str(start_date), str(end_date), float(initial_cash or 0), final, total, ann, calculate_max_drawdown(equity_curve), calculate_volatility(returns), calculate_sharpe(returns), calculate_win_rate(returns), len(allowed), int(rebalance_count or 0), calculate_turnover(allowed, initial_cash), int(risk_blocked_count or 0), {"max_drawdown_convention":"non_positive_ratio"})
