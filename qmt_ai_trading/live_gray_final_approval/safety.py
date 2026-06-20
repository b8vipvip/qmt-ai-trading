from __future__ import annotations
from pathlib import Path
from .models import LiveGrayFinalApprovalSeverity
FORBIDDEN=["xttrader","XtQuantTrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","查询资金","查询持仓","查询订单","查询成交","requests.post","smtp","sendMessage","webhook","--live-enabled","--execute-live","--real-send","live_enabled=True","execute_live=True","real_order_enabled=True","real_send=True","自动批准","自动approve","绕过风控","bypass Risk Gate","bypass Human Approval","auto live","auto approve","auto submit"]
WARN_CONTEXTS=("docs/","tests/","safety marker definitions","generated","final approval","signoff checklist","rollback approval","next seal plan","live_gray_final_approval_stage58")
def classify_live_gray_final_approval_marker(marker: str, context: str="") -> LiveGrayFinalApprovalSeverity:
    ctx=context.replace('\\','/')
    if any(w in ctx for w in WARN_CONTEXTS): return LiveGrayFinalApprovalSeverity.WARN
    return LiveGrayFinalApprovalSeverity.CRITICAL
def scan_live_gray_final_approval_text_for_forbidden_markers(text: str, context: str="") -> list[dict[str,str]]:
    return [{"marker":m,"severity":classify_live_gray_final_approval_marker(m,context).value,"context":context} for m in FORBIDDEN if m in text]
def assert_stage58_read_only(text: str="", context: str="actual executable") -> None:
    bad=[f for f in scan_live_gray_final_approval_text_for_forbidden_markers(text,context) if f["severity"]=="CRITICAL"]
    if bad: raise RuntimeError("Stage58 read-only boundary violation: "+", ".join(f["marker"] for f in bad))
def assert_no_xttrader_import(path: str|Path) -> None:
    p=Path(path); files=[p] if p.is_file() else [x for x in p.rglob('*.py') if '__pycache__' not in x.parts and 'live_gray_final_approval/safety.py' not in str(x).replace('\\','/')]
    bad=[]
    for f in files:
        txt=f.read_text(encoding='utf-8', errors='ignore')
        if 'xttrader' in txt or 'XtQuantTrader' in txt: bad.append(str(f))
    if bad: raise RuntimeError('xttrader import/call marker found: '+', '.join(bad))
