from __future__ import annotations
import json
from pathlib import Path
FORBIDDEN_TERMS=["execute_order","live_trade","auto_approve","bypass_risk","xttrader","XtQuantTrader","place_order","buy_now","sell_now","query_account","query_position","query_order","query_trade","send_email","send_sms","telegram_send","wechat_send","dingding_send"]
CRITICAL_TERMS={"execute_order","live_trade","xttrader","XtQuantTrader","place_order"}
ACCOUNT_TERMS={"query_account","query_position","query_order","query_trade"}
NOTIFICATION_TERMS={"send_email","send_sms","telegram_send","wechat_send","dingding_send"}
def scan_text(text:str):
    return sorted({t for t in FORBIDDEN_TERMS if t in text})
def scan_obj(obj):
    return scan_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str))
def scan_file(path:Path):
    try: return scan_text(path.read_text(encoding='utf-8', errors='replace'))
    except Exception: return []
