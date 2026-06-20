from __future__ import annotations
from pathlib import Path
from .models import LiveGrayFinalApprovalSeverity
FORBIDDEN=["xttrader","XtQuantTrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","查询资金","查询持仓","查询订单","查询成交","requests.post","smtp","sendMessage","webhook","--live-enabled","--execute-live","--real-send","live_enabled=True","execute_live=True","real_order_enabled=True","real_send=True","自动批准","自动approve","绕过风控","bypass Risk Gate","bypass Human Approval","auto live","auto approve","auto submit"]
GENERATED_REPORT_CONTEXTS=("qmt_dryrun_calibration_stage55/","real_cache_quality_stage56/","live_gray_candidate_stage57/","live_gray_final_approval_stage58/","docs/","tests/","validation_logs/")
SAFETY_NOTE_HINTS=("不调用","禁止调用","不真实下单","不查询真实账户","不查询资金","不查询持仓","不查询订单","不查询成交","不是实盘授权","generated markdown","generated json","safety note","safety marker definitions")
EXECUTABLE_DANGER_MARKERS={"xttrader","xtquanttrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","live_enabled=true","execute_live=true","real_order_enabled=true","real_send=true","--execute-live","--real-send"}
EXECUTABLE_SUFFIXES=(".py",".ps1",".json",".yaml",".yml")
def classify_live_gray_final_approval_marker(marker: str, context: str="", text: str="") -> LiveGrayFinalApprovalSeverity:
    ctx=str(context).replace('\\','/').lower()
    marker_lower=str(marker).lower()
    text_lower=str(text).lower()
    if any(part in ctx for part in GENERATED_REPORT_CONTEXTS):
        return LiveGrayFinalApprovalSeverity.WARN
    if any(hint in text or hint in text_lower for hint in SAFETY_NOTE_HINTS):
        return LiveGrayFinalApprovalSeverity.WARN
    if ctx.endswith(EXECUTABLE_SUFFIXES) and marker_lower in EXECUTABLE_DANGER_MARKERS:
        return LiveGrayFinalApprovalSeverity.CRITICAL
    if context in ("", "actual executable") and marker_lower in EXECUTABLE_DANGER_MARKERS:
        return LiveGrayFinalApprovalSeverity.CRITICAL
    return LiveGrayFinalApprovalSeverity.WARN
def scan_live_gray_final_approval_text_for_forbidden_markers(text: str, context: str="") -> list[dict[str,str]]:
    return [{"marker":m,"severity":classify_live_gray_final_approval_marker(m,context,text).value,"context":context} for m in FORBIDDEN if m in text]
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
