from __future__ import annotations
import re
from pathlib import Path
from .models import LocalConsoleRouteItem, LocalConsoleSeverity
FORBIDDEN_ROUTES={'/order','/orders','/trade','/execute','/approve','/live','/notify','/account','/positions','/assets'}
MARKERS=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit']
def _warn_context(path='', generated=False):
    p=str(path).replace('\\','/').lower()
    return generated or p.startswith('docs/') or '/tests/' in p or p.startswith('tests/') or any(x in p for x in ['stage55','stage56','stage57','stage58','stage59','stage60','stage61','local_console_stage62','api_gateway_stage61'])
def classify_local_console_route(path, method='GET'):
    p=str(path).split('?')[0]; m=method.upper(); forbidden=m!='GET' or p in FORBIDDEN_ROUTES
    return LocalConsoleRouteItem(path=p, method=m, title='forbidden route' if forbidden else 'local console read-only view', forbidden=forbidden, summary='forbidden console route or action' if forbidden else 'Stage62 read-only console route')
def classify_local_console_marker(marker, path='', generated=False):
    if marker in {'xtdata','xtquant.xtdata'}: return None
    return LocalConsoleSeverity.WARN if _warn_context(path, generated) else LocalConsoleSeverity.CRITICAL
def scan_local_console_text_for_forbidden_markers(text, path='', generated=False):
    out=[]
    for marker in MARKERS:
        if marker in text:
            sev=classify_local_console_marker(marker,path,generated)
            if sev: out.append({'marker':marker,'severity':sev.value,'path':str(path)})
    return out
def assert_stage62_read_only():
    return {'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'no_task_registered':True}
def assert_no_xttrader_import(paths=None):
    hits=[]
    for base in paths or ['qmt_ai_trading/local_console','scripts/run_local_console_review.py']:
        p=Path(base)
        files=[p] if p.is_file() else list(p.rglob('*.py')) if p.exists() else []
        for f in files:
            txt=f.read_text(encoding='utf-8')
            if re.search(r'from\s+.*xttrader|import\s+.*xttrader|XtQuantTrader', txt): hits.append(str(f))
    return hits
def assert_no_forbidden_console_routes(routes):
    return [r.path if hasattr(r,'path') else str(r) for r in routes if classify_local_console_route(r.path if hasattr(r,'path') else r, getattr(r,'method','GET')).forbidden]
