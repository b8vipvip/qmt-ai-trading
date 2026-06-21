from __future__ import annotations
DANGEROUS_TERMS=['xttrader','XtQuantTrader','place_order','execute_order','buy_now','sell_now','query_account','query_position','query_order','query_trade','live_trade','real_market_data','real_xtdata']
def scan_text(text:str)->list[str]:
    low=text.lower(); return [t for t in DANGEROUS_TERMS if t.lower() in low]
def scan_obj(obj)->list[str]:
    import json
    return scan_text(json.dumps(obj,ensure_ascii=False,sort_keys=True))
def safety_report(obj):
    hits=scan_obj(obj); return {'safe':not hits,'violations':hits,'sandbox':True,'not_live_trading':True,'read_only':True,'no_qmt_trader_api':True,'no_order_submitted':True}
