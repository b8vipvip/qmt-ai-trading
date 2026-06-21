from __future__ import annotations
from .safety import with_safety

def calculate_metrics(shadow, context):
    rows=shadow.get('shadow_replay',[]); n=len(rows) or 1
    total=sum(r.get('mock_return',0) for r in rows)
    maxdd=max([r.get('max_drawdown',0) for r in rows] or [0])
    vol=round((sum((r.get('mock_return',0)-total/n)**2 for r in rows)/n)**0.5,4)
    risk_dec=context.get('factor_risk_decisions') or []
    rejected=sum(1 for d in risk_dec if isinstance(d,dict) and d.get('allowed') is False)
    approved=sum(1 for d in risk_dec if isinstance(d,dict) and d.get('allowed') is True)
    return with_safety({'total_return':round(total,4),'annualized_return':round(total*12,4),'max_drawdown':maxdd,'volatility':vol,'sharpe_like':round(total/(vol or 0.01),4),'win_rate':round(sum(1 for r in rows if r.get('win'))/n,4),'trade_count':len(rows),'turnover':round(len(rows)*0.1,4),'avg_holding_days':round(sum(r.get('holding_days',0) for r in rows)/n,2),'risk_rejected_count':rejected,'approved_dry_run_count':approved,'data_quality':context.get('data_quality','fallback_safe')})
