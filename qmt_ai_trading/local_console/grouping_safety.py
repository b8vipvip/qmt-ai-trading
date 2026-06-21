from __future__ import annotations
import re
from .grouping_models import LocalConsoleGroupingSeverity, GroupingFrontendSafetyFinding
ALLOWED_HASH_ROUTES=['#/dashboard','#/reports','#/filters','#/warnings','#/blocking-reasons','#/manifest','#/validation','#/scheduler','#/safety','#/api','#/next']
FORBIDDEN_HASH_ROUTES=['#/order','#/orders','#/trade','#/execute','#/approve','#/live','#/notify','#/account','#/positions','#/assets']
FORBIDDEN_MARKERS=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post',"fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","fetch('/positions')","fetch('/assets')","fetch('/live')","fetch('/notify')","fetch('/execute')",'XMLHttpRequest','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit','tradeButton','approveButton','orderButton','liveButton','notifyButton','accountButton','positionButton','executeButton','submitOrder','approveOrder','sendNotification']
DANGEROUS_ACTIONS=[m for m in FORBIDDEN_MARKERS if m not in {'xttrader','查询资金','查询持仓','查询订单','查询成交'}]

def assert_stage69_read_only(read_only=True,dry_run_only=True,no_trade_authorization=True):
    if not (read_only and dry_run_only and no_trade_authorization): raise ValueError('Stage69 must remain read_only/dry_run_only/no_trade_authorization')

def classify_grouping_hash_route(route):
    return LocalConsoleGroupingSeverity.CRITICAL if route in FORBIDDEN_HASH_ROUTES else LocalConsoleGroupingSeverity.INFO

def assert_no_forbidden_grouping_routes(routes):
    bad=[r for r in routes if r in FORBIDDEN_HASH_ROUTES]
    if bad: raise ValueError('forbidden grouping routes: '+', '.join(bad))

def classify_grouping_marker(marker,path,context='',executable=False,generated=False):
    if marker in {'xtdata','xtquant.xtdata'}: return LocalConsoleGroupingSeverity.INFO
    lower=(context or '').lower(); p=(path or '').lower()
    safe_phrase=('不调用' in context or '不查询' in context or '不是实盘' in context or '安全' in context or 'read_only' in lower or 'safety' in p or generated or p.endswith(('.md','.json')) or 'data_bundle' in p)
    if marker in FORBIDDEN_HASH_ROUTES or marker in DANGEROUS_ACTIONS or marker in {'tradeButton','approveButton','orderButton','liveButton'}:
        return LocalConsoleGroupingSeverity.CRITICAL if executable or p.endswith('.js') or 'app.js' in p else LocalConsoleGroupingSeverity.WARN
    if marker in {'xttrader','XtQuantTrader','place_order','query_stock_asset','查询资金','查询持仓','查询订单','查询成交'} and safe_phrase:
        return LocalConsoleGroupingSeverity.WARN
    return LocalConsoleGroupingSeverity.CRITICAL if executable else LocalConsoleGroupingSeverity.WARN

def scan_grouping_assets_for_forbidden_markers(assets, generated=False):
    findings=[]
    for path,text in (assets or {}).items():
        executable=str(path).endswith(('.js','.py')) and not generated
        for m in FORBIDDEN_MARKERS:
            if m in text:
                findings.append(GroupingFrontendSafetyFinding(m,path,classify_grouping_marker(m,path,text,executable,generated),text[:160],'Stage69 marker classification'))
    return findings

def assert_no_forbidden_grouping_actions(js_text):
    findings=scan_grouping_assets_for_forbidden_markers({'app.js':js_text})
    bad=[f for f in findings if f.severity==LocalConsoleGroupingSeverity.CRITICAL]
    if bad: raise ValueError('forbidden grouping frontend actions: '+', '.join(f.marker for f in bad))

def assert_no_xttrader_import(text=''):
    if re.search(r'(^|\n)\s*(from|import)\s+.*xttrader', text): raise ValueError('xttrader import is forbidden')

def assert_no_forbidden_grouping_frontend_actions(js_text=''):
    assert_no_forbidden_grouping_actions(js_text)
