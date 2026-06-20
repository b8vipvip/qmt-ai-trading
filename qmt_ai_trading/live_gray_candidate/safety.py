from __future__ import annotations
from pathlib import Path
from .models import LiveGrayCandidateSeverity

FORBIDDEN = ["xttrader","XtQuantTrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","查询资金","查询持仓","查询订单","查询成交","requests.post","smtp","sendMessage","webhook","--live-enabled","--execute-live","--real-send","live_enabled=True","execute_live=True","real_order_enabled=True","real_send=True","自动批准","自动approve","绕过风控","bypass Risk Gate","bypass Human Approval","auto live","auto approve","auto submit"]
WARN_CONTEXTS=("docs/","tests/","safety marker definitions","generated","gray candidate","risk limit","approval checklist","rollback plan","next plan")

def classify_live_gray_candidate_marker(marker: str, context: str="") -> LiveGrayCandidateSeverity:
    ctx=context.replace("\\","/")
    if any(w in ctx for w in WARN_CONTEXTS):
        return LiveGrayCandidateSeverity.WARN
    return LiveGrayCandidateSeverity.CRITICAL

def scan_live_gray_candidate_text_for_forbidden_markers(text: str, context: str="") -> list[dict[str,str]]:
    findings=[]
    for m in FORBIDDEN:
        if m in text:
            findings.append({"marker":m,"severity":classify_live_gray_candidate_marker(m, context).value,"context":context})
    return findings

def assert_stage57_read_only(text: str="", context: str="actual executable") -> None:
    critical=[f for f in scan_live_gray_candidate_text_for_forbidden_markers(text, context) if f["severity"]==LiveGrayCandidateSeverity.CRITICAL.value]
    if critical:
        raise RuntimeError("Stage57 read-only boundary violation: "+", ".join(f["marker"] for f in critical))

def assert_no_xttrader_import(path: str|Path) -> None:
    p=Path(path)
    if p.is_file():
        files=[p]
    else:
        files=[x for x in p.rglob("*.py") if "__pycache__" not in x.parts]
    bad=[]
    for f in files:
        txt=f.read_text(encoding="utf-8", errors="ignore")
        if "xttrader" in txt or "XtQuantTrader" in txt:
            bad.append(str(f))
    if bad:
        raise RuntimeError("xttrader import/call marker found: "+", ".join(bad))
