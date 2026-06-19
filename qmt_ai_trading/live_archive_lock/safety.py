from __future__ import annotations
from .models import LiveArchiveLockSeverity
FORBIDDEN_MARKERS=['xttrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit']
def assert_stage51_read_only(read_only=True,dry_run_only=True,no_trade_authorization=True,live_trading_enabled=False,no_task_registered=True):
    if not read_only or not dry_run_only or not no_trade_authorization or live_trading_enabled or not no_task_registered: raise ValueError('Stage51 must remain read-only/dry-run/no-trade/no-task-registered.')
def classify_archive_lock_marker(marker:str, context:str='', path:str='') -> LiveArchiveLockSeverity:
    text=f'{context} {path}'.lower()
    warn_contexts=['docs/','tests/','safety.py','live_archive_lock_stage51','live_archive_lock/','final lock review','archive lock','human closure recheck','next readonly check plan','generated']
    if any(x in text for x in warn_contexts): return LiveArchiveLockSeverity.WARN
    critical_contexts=['actual executable','execute','gateway','order.py','account','real notification','live']
    if any(x in text for x in critical_contexts): return LiveArchiveLockSeverity.CRITICAL
    return LiveArchiveLockSeverity.WARN
def scan_archive_lock_text_for_forbidden_markers(text:str, context:str='', path:str=''):
    found=[]; lower=text.lower()
    for m in FORBIDDEN_MARKERS:
        if m.lower() in lower:
            found.append({'marker':m,'severity':classify_archive_lock_marker(m,context,path).value,'context':context,'path':path})
    return found
