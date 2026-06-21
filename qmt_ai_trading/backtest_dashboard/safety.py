from __future__ import annotations
import json

SAFETY_FLAGS={
 'dry_run': True,'not_live_trading': True,'research_only': True,'no_order_submitted': True,
 'no_qmt_trader_api': True,'requires_risk_gate': True,'requires_human_approval': True,
}
FORBIDDEN_TERMS=['live_trade','execute_order','auto_approve','bypass_risk','xttrader','place_order','XtQuantTrader','query_asset','query_position','query_order','query_trade']
DISCLAIMER='该结果仅用于前端联调和研究展示，不能作为实盘依据。'

def scan_text(obj):
    text=json.dumps(obj, ensure_ascii=False).lower() if not isinstance(obj,str) else obj.lower()
    hits=[t for t in FORBIDDEN_TERMS if t.lower() in text]
    return {'unsafe': bool(hits), 'forbidden_terms': hits, **SAFETY_FLAGS}

def with_safety(payload):
    out=dict(payload)
    out.update(SAFETY_FLAGS)
    out.setdefault('fallback_used', True)
    out.setdefault('mock_data', True)
    out.setdefault('backtest_mode','mock_shadow')
    out.setdefault('disclaimer', DISCLAIMER)
    out.update(scan_text(out))
    return out
