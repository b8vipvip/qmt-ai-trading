from __future__ import annotations
from pathlib import Path
from .models import LiveFinalArchiveSeverity
FORBIDDEN=["xttrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","查询资金","查询持仓","查询订单","查询成交","requests.post","smtp","sendMessage","webhook","--live-enabled","--execute-live","--real-send","live_enabled=True","execute_live=True","real_order_enabled=True","real_send=True","自动批准","自动approve","绕过风控","bypass Risk Gate","bypass Human Approval","auto live","auto approve","auto submit"]
WARN_HINTS=("docs/","tests/","safety.py","live_final_archive","remediation","human_closure","next_readonly_check","material_final_archive","stage50","generated")
CRITICAL_HINTS=("execute","executor","gateway","order","account","xttrader","live_runner","notification")
def classify_final_archive_marker(marker:str, context:str="", path:str|Path="") -> LiveFinalArchiveSeverity:
    p=str(path).replace('\\','/'); c=context.lower(); pl=p.lower()
    if any(h in pl for h in WARN_HINTS) or any(h in c for h in ("definition","定义","声明","不调用","不真实","不是实盘","forbidden marker")): return LiveFinalArchiveSeverity.WARN
    if any(h in pl for h in CRITICAL_HINTS) or any(h in c for h in ("actual executable","真实执行","call ","import xttrader")): return LiveFinalArchiveSeverity.CRITICAL
    return LiveFinalArchiveSeverity.WARN
def scan_final_archive_text_for_forbidden_markers(text:str, *, context:str="", path:str|Path=""):
    found=[]
    low=text.lower()
    for m in FORBIDDEN:
        if m.lower() in low:
            found.append({"marker":m,"severity":classify_final_archive_marker(m,context,path).value,"path":str(path),"context":context})
    return found
def assert_stage50_read_only(read_only=True,dry_run_only=True,no_trade_authorization=True,live_trading_enabled=False,no_task_registered=True):
    if not read_only or not dry_run_only or not no_trade_authorization or live_trading_enabled or not no_task_registered:
        raise ValueError("Stage50 must remain read_only/dry_run_only/no_trade_authorization/live disabled/no_task_registered")
