from __future__ import annotations
from pathlib import Path
from .models import RealCacheQualitySeverity
FORBIDDEN=["xttrader","XtQuantTrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","查询资金","查询持仓","查询订单","查询成交","requests.post","smtp","sendMessage","webhook","--live-enabled","--execute-live","--real-send","live_enabled=True","execute_live=True","real_order_enabled=True","real_send=True","自动批准","自动approve","绕过风控","bypass Risk Gate","bypass Human Approval","auto live","auto approve","auto submit"]
def classify_real_cache_quality_marker(marker:str, context:str="") -> RealCacheQualitySeverity:
    ctx=context.lower()
    if any(x in ctx for x in ["docs/","tests/","generated","real_cache_quality","gap fill","field quality","next plan","marker definition","安全边界","不得","禁止","不调用","不真实"]): return RealCacheQualitySeverity.WARN
    if marker in {"xtdata","xtquant.xtdata"}: return RealCacheQualitySeverity.INFO
    return RealCacheQualitySeverity.CRITICAL
def scan_real_cache_quality_text_for_forbidden_markers(text:str, context:str=""):
    return [(m, classify_real_cache_quality_marker(m, context)) for m in FORBIDDEN if m in text]
def assert_stage56_read_only(text:str="", context:str="runtime") -> None:
    bad=[m for m,s in scan_real_cache_quality_text_for_forbidden_markers(text, context) if s==RealCacheQualitySeverity.CRITICAL]
    if bad: raise RuntimeError("Stage56 forbidden live marker: "+", ".join(bad))
def assert_no_xttrader_import(path: str|Path) -> None:
    p=Path(path); text=p.read_text(encoding='utf-8') if p.exists() else str(path)
    if "xttrader" in text or "XtQuantTrader" in text: raise RuntimeError("xttrader import/call is forbidden in Stage56")
