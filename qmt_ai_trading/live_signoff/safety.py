from __future__ import annotations
from pathlib import Path
from .models import LiveSignoffCategory as C, LiveSignoffEvidence, LiveSignoffSeverity as Sev, LiveSignoffStatus as S
FORBIDDEN_MARKERS=("xttrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","查询资金","查询持仓","查询订单","查询成交","requests.post","smtp","sendMessage","webhook","--live-enabled","--execute-live","--real-send","live_enabled=True","execute_live=True","real_order_enabled=True","real_send=True","自动批准","自动approve","绕过风控","bypass Risk Gate","bypass Human Approval","auto live","auto approve","auto submit")
BENIGN=("docs/","tests/","safety.py","live_signoff_stage46","live_signoff","manual_signoff","incident_rehearsal","runbook review","marker definitions","forbidden marker","不调用 xttrader","不是实盘授权","read-only","dry-run")
def classify_signoff_marker(path: str|Path, marker: str, text_context: str="") -> Sev:
    p=str(path).replace('\\','/').lower(); ctx=text_context.lower()
    if any(b.lower() in p or b.lower() in ctx for b in BENIGN): return Sev.WARN
    return Sev.CRITICAL
def scan_signoff_text_for_forbidden_markers(text: str, path: str|Path="") -> list[LiveSignoffEvidence]:
    out=[]; low=text.lower()
    for m in FORBIDDEN_MARKERS:
        if m.lower() in low:
            sev=classify_signoff_marker(path,m,text)
            out.append(LiveSignoffEvidence(evidence_id=f"stage46-marker-{len(out)+1}",category=C.QMT_BOUNDARY,status=S.FAIL if sev==Sev.CRITICAL else S.WARN,severity=sev,path=str(path),title=m,summary=f"Forbidden marker '{m}' found in Stage46 signoff scan; severity={sev.value}."))
    return out
def assert_stage46_read_only(read_only: bool=True, dry_run_only: bool=True, no_trade_authorization: bool=True, live_trading_enabled: bool=False) -> None:
    if not read_only or not dry_run_only or not no_trade_authorization or live_trading_enabled:
        raise RuntimeError("Stage46 must stay read_only=True, dry_run_only=True, no_trade_authorization=True, live_trading_enabled=False")
