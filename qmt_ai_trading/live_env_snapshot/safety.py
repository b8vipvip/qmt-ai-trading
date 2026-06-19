from __future__ import annotations
from pathlib import Path
from .models import ConfigFreezeReviewItem, LiveEnvSnapshotCategory as C, LiveEnvSnapshotSeverity as Sev, LiveEnvSnapshotStatus as S

FORBIDDEN_MARKERS=("xttrader","place_order","submit_order","order_stock","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","查询资金","查询持仓","查询订单","查询成交","requests.post","smtp","sendMessage","webhook","--live-enabled","--execute-live","--real-send","live_enabled=True","execute_live=True","real_order_enabled=True","real_send=True","自动批准","自动approve","绕过风控","bypass Risk Gate","bypass Human Approval","auto live","auto approve","auto submit")

def classify_env_snapshot_marker(path: str|Path, marker: str, text_context: str = "") -> Sev:
    p=str(path).replace('\\','/').lower(); ctx=text_context.lower()
    if '/docs/' in f'/{p}' or '/tests/' in f'/{p}' or 'safety.py' in p or 'marker' in ctx or 'definition' in ctx:
        return Sev.WARN
    if 'live_env_snapshot_stage44' in p or 'config_freeze' in p or 'live_env_snapshot' in p and p.endswith(('.md','.json')):
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
