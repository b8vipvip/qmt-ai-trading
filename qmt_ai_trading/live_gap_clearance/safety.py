from __future__ import annotations
from .models import LiveGapClearanceSeverity
FORBIDDEN_MARKERS=['xttrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit']
def assert_stage54_read_only(read_only=True,dry_run_only=True,no_trade_authorization=True,live_trading_enabled=False,no_task_registered=True):
    if not read_only or not dry_run_only or not no_trade_authorization or live_trading_enabled or not no_task_registered:
        raise ValueError('Stage54 must remain read-only/dry-run and must not authorize live trading or register tasks.')
def classify_gap_clearance_marker(marker:str, context:str=''):
    c=(context or '').lower(); safe=('docs/' in c or 'tests/' in c or 'safety marker' in c or 'forbidden marker' in c or 'generated gap clearance' in c or 'evidence remediation' in c or 'human closure recheck' in c or 'next readonly check plan' in c or 'markdown' in c or 'report' in c)
    return LiveGapClearanceSeverity.WARN if safe else LiveGapClearanceSeverity.CRITICAL
def scan_gap_clearance_text_for_forbidden_markers(text:str, context:str=''):
    hits=[]
    for m in FORBIDDEN_MARKERS:
        if m.lower() in (text or '').lower(): hits.append({'marker':m,'severity':classify_gap_clearance_marker(m,context).value,'context':context})
    return hits
