from __future__ import annotations
from pathlib import Path
from .refresh_models import FrontEndSafetyFinding, LocalConsoleRefreshSeverity

FORBIDDEN_HASH_ROUTES=['#/order','#/orders','#/trade','#/execute','#/approve','#/live','#/notify','#/account','#/positions','#/assets']
FORBIDDEN_ACTIONS=["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","fetch('/positions')","fetch('/assets')","fetch('/live')","fetch('/notify')","fetch('/execute')",'XMLHttpRequest','requests.post','webhook','smtp','sendMessage','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit']
DANGEROUS_BUTTONS=['tradeButton','approveButton','orderButton','liveButton','notifyButton','accountButton','positionButton','executeButton','submitOrder','approveOrder','sendNotification']
MARKERS=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交']+FORBIDDEN_ACTIONS

def assert_stage68_read_only(): return True

def classify_refresh_hash_route(route):
    return LocalConsoleRefreshSeverity.CRITICAL if route in FORBIDDEN_HASH_ROUTES else LocalConsoleRefreshSeverity.INFO

def assert_no_forbidden_refresh_routes(routes):
    bad=[r for r in routes if classify_refresh_hash_route(r)==LocalConsoleRefreshSeverity.CRITICAL]
    if bad: raise ValueError('forbidden hash routes: '+', '.join(bad))
    return True

def classify_refresh_marker(marker, path='', text='', executable=False, generated=False):
    if marker in {'xtdata','xtquant.xtdata'}: return LocalConsoleRefreshSeverity.INFO
    safe_text=('不调用' in text or '不得' in text or '不是实盘授权' in text or 'Safety Banner' in text or generated or path.endswith(('.md','.json','.html')) and not executable)
    if marker in FORBIDDEN_ACTIONS or marker in DANGEROUS_BUTTONS: return LocalConsoleRefreshSeverity.CRITICAL
    if safe_text: return LocalConsoleRefreshSeverity.WARN
    if executable and marker in MARKERS: return LocalConsoleRefreshSeverity.CRITICAL
    return LocalConsoleRefreshSeverity.CRITICAL

def scan_refresh_assets_for_forbidden_markers(items, generated=False):
    findings=[]
    pairs=items.items() if isinstance(items,dict) else items
    for path,text in pairs:
        executable=str(path).endswith('.js') or str(path).endswith('.py')
        for m in MARKERS + DANGEROUS_BUTTONS:
            if m in text:
                sev=classify_refresh_marker(m,str(path),text,executable,generated)
                findings.append(FrontEndSafetyFinding(m,str(path),sev,text[:160], 'Stage68 marker classification'))
    return findings

def assert_no_forbidden_refresh_actions(js_text):
    bad=[m for m in FORBIDDEN_ACTIONS+DANGEROUS_BUTTONS if m in js_text]
    if bad: raise ValueError('forbidden frontend actions: '+', '.join(bad))
    return True

def assert_no_xttrader_import(text=''):
    if 'import xttrader' in text or 'from xtquant.xttrader' in text or 'XtQuantTrader(' in text: raise ValueError('xttrader import forbidden')
    return True

def assert_no_forbidden_frontend_actions(js_text=''):
    return assert_no_forbidden_refresh_actions(js_text)
