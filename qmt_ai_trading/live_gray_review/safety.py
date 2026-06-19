from __future__ import annotations
from pathlib import Path
from .models import LiveGrayReviewCategory as C, LiveGrayReviewChecklistItem, LiveGrayReviewSeverity as Sev, LiveGrayReviewStatus as S

FORBIDDEN_MARKERS=["xttrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","查询资金","查询持仓","查询订单","查询成交","requests.post","smtp","sendMessage","webhook","--live-enabled","--execute-live","--real-send","live_enabled=True","execute_live=True","real_order_enabled=True","real_send=True","自动批准","自动approve","绕过风控","bypass Risk Gate","bypass Human Approval","auto live","auto approve","auto submit"]
SAFE_CONTEXT_WORDS=["forbidden","禁止","不得","不调用","不下单","不查询","不真实","只读","read-only","dry-run","marker","FORBIDDEN_MARKERS","Safety Note","安全","不会","不能","preview","不是实盘授权"]

def _norm(path: str|Path)->str: return str(path).replace('\\','/').lower()
def _docs_tests_or_safety(path: str|Path)->bool:
    p=_norm(path)
    return p.startswith(('docs/','tests/')) or '/docs/' in p or '/tests/' in p or p.endswith('safety.py') or p.endswith('.md')
def _safe_line(line: str)->bool:
    low=line.lower(); return any(w.lower() in low for w in SAFE_CONTEXT_WORDS)

def classify_review_marker(marker: str, path: str|Path="", line: str="") -> tuple[S, Sev, C, str]:
    low=marker.lower()
    if _docs_tests_or_safety(path) or _safe_line(line):
        return S.WARN, Sev.WARN, C.SYSTEM, f"Forbidden marker {marker} appears only in documentation/test/safety-marker or generated review context."
    if any(x in low for x in ["xttrader","query_stock","查询资金","查询持仓","查询订单","查询成交"]): cat=C.QMT_BOUNDARY
    elif any(x in low for x in ["order","submit","place"]): cat=C.QMT_BOUNDARY
    elif any(x in low for x in ["post","smtp","sendmessage","webhook","real-send"]): cat=C.NOTIFICATION_DRY_RUN
    elif any(x in low for x in ["approve","批准","bypass"]): cat=C.HUMAN_APPROVAL
    else: cat=C.SYSTEM
    return S.FAIL, Sev.CRITICAL, cat, f"Forbidden executable Stage42 marker {marker} detected."

def scan_review_text_for_forbidden_markers(text: str, path: str|Path="stage42-context") -> list[LiveGrayReviewChecklistItem]:
    findings=[]
    for no,line in enumerate((text or '').splitlines(),1):
        for marker in FORBIDDEN_MARKERS:
            if marker in line:
                status,severity,category,msg=classify_review_marker(marker,path,line)
                findings.append(LiveGrayReviewChecklistItem(f"stage42-marker-{len(findings)+1:04d}",category,status,severity,str(path),no,marker,msg,"Keep Stage42 read-only; remove executable live/account/notification action."))
    return findings

def assert_stage42_read_only(text: str="", path: str|Path="stage42-context") -> None:
    critical=[x for x in scan_review_text_for_forbidden_markers(text,path) if x.severity==Sev.CRITICAL or x.status==S.FAIL]
    if critical:
        first=critical[0]
        raise ValueError(f"Stage42 read-only violation: {first.path}:{first.line_number} {first.marker}")
