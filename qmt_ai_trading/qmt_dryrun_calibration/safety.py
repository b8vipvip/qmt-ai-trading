from __future__ import annotations
from dataclasses import dataclass
from .models import QmtDryrunCalibrationSeverity
FORBIDDEN=["xttrader","XtQuantTrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","查询资金","查询持仓","查询订单","查询成交","requests.post","smtp","sendMessage","webhook","--live-enabled","--execute-live","--real-send","live_enabled=True","execute_live=True","real_order_enabled=True","real_send=True","自动批准","自动approve","绕过风控","bypass Risk Gate","bypass Human Approval","auto live","auto approve","auto submit"]
@dataclass
class MarkerFinding:
    marker:str; severity:QmtDryrunCalibrationSeverity|str; context:str; summary:str

def classify_qmt_dryrun_marker(marker:str, context:str=""):
    c=context.lower()
    if any(x in c for x in ["docs/","tests/","generated","qmt_dryrun_calibration","xtdata capability","whitelist","next plan","safety marker"]):
        return QmtDryrunCalibrationSeverity.WARN
    if marker in {"xttrader","XtQuantTrader"} or any(x in marker for x in ["order","query_stock"]) or marker in FORBIDDEN:
        return QmtDryrunCalibrationSeverity.CRITICAL
    return QmtDryrunCalibrationSeverity.WARN

def scan_qmt_dryrun_calibration_text_for_forbidden_markers(text:str, context:str=""):
    out=[]
    for m in FORBIDDEN:
        if m in text:
            sev=classify_qmt_dryrun_marker(m, context)
            out.append(MarkerFinding(m, sev, context, f"{m} marker classified as {sev.value if hasattr(sev,'value') else sev}"))
    return out

def assert_stage55_read_only(read_only=True,dry_run_only=True,no_trade_authorization=True,live_trading_enabled=False,no_task_registered=True):
    if not read_only or not dry_run_only or not no_trade_authorization or live_trading_enabled or not no_task_registered:
        raise ValueError("Stage55 must stay read_only/dry_run_only/no_trade_authorization and must not register tasks")

def assert_no_xttrader_import(text:str=""):
    findings=[f for f in scan_qmt_dryrun_calibration_text_for_forbidden_markers(text, "actual executable") if str(f.severity)==QmtDryrunCalibrationSeverity.CRITICAL or getattr(f.severity,'value',None)=="CRITICAL"]
    if findings: raise ValueError("Forbidden Stage55 marker: "+", ".join(f.marker for f in findings))
