from __future__ import annotations
import ast
from pathlib import Path
from .models import PreGrayFinalReviewSeverity
FORBIDDEN_MARKERS=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit']
GENERATED_HINTS=['docs/','tests/','stage55','stage56','stage57','stage58','stage59','stage60','generated','review','go-no-go','checklist','plan','.md','.json']
def classify_pre_gray_final_review_marker(marker: str, context: str='', path: str='') -> PreGrayFinalReviewSeverity:
    low=(context+' '+path).lower()
    if 'xtdata' in marker.lower() and 'xttrader' not in marker.lower(): return PreGrayFinalReviewSeverity.INFO
    if any(h in low for h in GENERATED_HINTS) or ('不调用' in context and marker in ('xttrader','XtQuantTrader')): return PreGrayFinalReviewSeverity.WARN
    return PreGrayFinalReviewSeverity.CRITICAL
def scan_pre_gray_final_review_text_for_forbidden_markers(text: str, path: str=''):
    hits=[]
    for m in FORBIDDEN_MARKERS:
        if m in text:
            hits.append({'marker':m,'severity':classify_pre_gray_final_review_marker(m,text,path),'path':path})
    return hits
def assert_stage60_read_only(text: str='', path: str='') -> None:
    critical=[h for h in scan_pre_gray_final_review_text_for_forbidden_markers(text,path) if h['severity']==PreGrayFinalReviewSeverity.CRITICAL]
    if critical: raise RuntimeError('Stage60 read-only boundary violation: '+', '.join(h['marker'] for h in critical))
def assert_no_xttrader_import(path: str|Path) -> None:
    p=Path(path); tree=ast.parse(p.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if 'xttrader' in a.name or a.name=='XtQuantTrader': raise RuntimeError(f'xttrader import forbidden: {p}')
        if isinstance(node, ast.ImportFrom) and node.module and 'xttrader' in node.module:
            raise RuntimeError(f'xttrader import forbidden: {p}')
