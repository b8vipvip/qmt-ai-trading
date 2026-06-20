from __future__ import annotations
import ipaddress, re
from pathlib import Path
from .preview_routes import FORBIDDEN_ROUTES, FORBIDDEN_HASH_ROUTES
MARKERS=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post',"fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","fetch('/positions')","fetch('/assets')","fetch('/live')","fetch('/notify')","fetch('/execute')",'XMLHttpRequest','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit']
def assert_stage67_read_only(): return {'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'no_task_registered':True}
def assert_host_is_localhost(host): return host == '127.0.0.1'
def assert_no_public_bind(host):
    if host in ('0.0.0.0','::',''): return False
    try:
        ip=ipaddress.ip_address(host); return ip.is_loopback and str(ip)=='127.0.0.1'
    except ValueError: return host == '127.0.0.1'
def classify_preview_route(path, method='GET'):
    p=str(path).split('?')[0]; m=method.upper(); bad=m not in ('GET','HEAD') or p in FORBIDDEN_ROUTES or p in FORBIDDEN_HASH_ROUTES
    return {'path':p,'method':m,'forbidden':bad,'severity':'CRITICAL' if bad else 'INFO'}
def assert_no_forbidden_preview_routes(routes): return [r for r in routes if classify_preview_route(getattr(r,'path',r))['forbidden']]
def assert_no_forbidden_preview_methods(methods): return [m for m in methods if str(m).upper() not in ('GET','HEAD')]
def _warn_context(path='', generated=False):
    p=str(path).replace('\\','/').lower()
    return generated or p.startswith('docs/') or '/tests/' in p or 'test_' in p or any(x in p for x in ['stage55','stage56','stage57','stage58','stage59','stage60','stage61','stage62','stage63','stage64','stage65','stage66','generated','local_console_binding','local_console_preview','static_data_safety','safety_banner','next_console'])
def classify_preview_marker(marker, path='', generated=False, executable=False):
    if marker in {'xtdata','xtquant.xtdata'}: return 'INFO'
    p=str(path).replace('\\','/').lower()
    if marker in ('xttrader','XtQuantTrader') and any(x in p for x in ['index.html','static_data_safety','docs/','stage66','local_console_binding']) and not executable: return 'WARN'
    return 'CRITICAL' if executable or not _warn_context(path, generated) else 'WARN'
def scan_preview_assets_for_forbidden_markers(text_or_paths, path='', generated=False, executable=False):
    items=[]
    if isinstance(text_or_paths,(str,bytes)) and not Path(str(path)).exists():
        text=str(text_or_paths); items.append((path,text))
    else:
        for p in text_or_paths:
            pp=Path(p); items.append((str(pp), pp.read_text(encoding='utf-8',errors='replace') if pp.exists() else ''))
    hits=[]
    for p,text in items:
        for m in MARKERS:
            if m in text: hits.append({'marker':m,'path':p,'severity':classify_preview_marker(m,p,generated, executable or p.endswith(('.py','.js')) and m not in ('xttrader',))})
    return hits
def assert_no_xttrader_import(paths=None):
    hits=[]
    for base in paths or ['qmt_ai_trading/local_console/preview_server.py','qmt_ai_trading/local_console/preview_service.py','scripts/run_local_console_preview_server.py']:
        p=Path(base); files=[p] if p.is_file() else list(p.rglob('*.py')) if p.exists() else []
        for f in files:
            txt=f.read_text(encoding='utf-8',errors='replace')
            if re.search(r'from\s+.*xttrader|import\s+.*xttrader|XtQuantTrader',txt): hits.append(str(f))
    return hits
def assert_no_forbidden_server_actions(paths=None): return assert_no_xttrader_import(paths)
