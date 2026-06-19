from __future__ import annotations
from pathlib import Path
from .models import ConfigFreezeReviewItem, LiveEnvSnapshotCategory as C, LiveEnvSnapshotSeverity as Sev, LiveEnvSnapshotStatus as S

GENERATED_REPORT_DIR_MARKERS=(
    'live_env_snapshot_stage44', 'live_env_snapshot',
    'live_signature_freeze_stage43', 'live_signature_freeze',
    'live_gray_review_stage42', 'live_gray_ledger_stage41',
    'redline_review_stage40', 'generated review package',
    'generated signature', 'generated freeze', 'generated env snapshot',
)
GENERATED_REPORT_SUFFIXES=('.md','.json')
BENIGN_TEXT_MARKERS=(
    'safety note', 'human checklist', '不调用 xttrader', 'does not call xttrader',
    'does not import/call xttrader', '未调用 xttrader', 'not trade authorization',
    'read-only', 'dry-run only', '不是实盘授权', '不是真实执行路径',
)

FORBIDDEN_MARKERS=("xttrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","查询资金","查询持仓","查询订单","查询成交","requests.post","smtp","sendMessage","webhook","--live-enabled","--execute-live","--real-send","live_enabled=True","execute_live=True","real_order_enabled=True","real_send=True","自动批准","自动approve","绕过风控","bypass Risk Gate","bypass Human Approval","auto live","auto approve","auto submit")

def _is_generated_report_context(path: str, ctx: str) -> bool:
    if path.endswith(GENERATED_REPORT_SUFFIXES) and any(token in path for token in GENERATED_REPORT_DIR_MARKERS):
        return True
    if any(token in ctx for token in GENERATED_REPORT_DIR_MARKERS):
        return True
    return False

def _is_benign_text_context(path: str, ctx: str) -> bool:
    if path.endswith(GENERATED_REPORT_SUFFIXES) and any(token in ctx for token in BENIGN_TEXT_MARKERS):
        return True
    return False

def classify_env_snapshot_marker(path: str|Path, marker: str, text_context: str = "") -> Sev:
    p=str(path).replace('\\','/').lower(); ctx=text_context.lower()
    if _is_generated_report_context(p, ctx) or _is_benign_text_context(p, ctx):
        return Sev.WARN
    if '/docs/' in f'/{p}' or '/tests/' in f'/{p}' or 'safety.py' in p or 'marker' in ctx or 'definition' in ctx:
        return Sev.WARN
    return Sev.CRITICAL

def scan_env_snapshot_text_for_forbidden_markers(text: str, path: str|Path = "") -> list[ConfigFreezeReviewItem]:
    items=[]
    for marker in FORBIDDEN_MARKERS:
        if marker.lower() in text.lower():
            sev=classify_env_snapshot_marker(path, marker, text)
            items.append(ConfigFreezeReviewItem(item_id=f"stage44-marker-{len(items)+1}", category=C.QMT_BOUNDARY, status=S.FAIL if sev==Sev.CRITICAL else S.WARN, severity=sev, name=marker, value=str(path), summary=f"Forbidden marker '{marker}' found in read-only scan; severity={sev.value}."))
    return items

def assert_stage44_read_only(read_only: bool=True, dry_run_only: bool=True, no_trade_authorization: bool=True, live_trading_enabled: bool=False) -> None:
    if not read_only or not dry_run_only or not no_trade_authorization or live_trading_enabled:
        raise RuntimeError("Stage44 must stay read_only=True, dry_run_only=True, no_trade_authorization=True, live_trading_enabled=False")
