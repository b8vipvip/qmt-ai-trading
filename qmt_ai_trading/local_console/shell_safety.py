from __future__ import annotations
import re
from pathlib import Path
FORBIDDEN_ROUTES={'#/order','#/orders','#/trade','#/execute','#/approve','#/live','#/notify','#/account','#/positions','#/assets'}
MARKERS=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post',"fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","fetch('/positions')","fetch('/assets')","fetch('/live')","fetch('/notify')","fetch('/execute')",'XMLHttpRequest','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit','tradeButton','approveButton','orderButton','liveButton']
def assert_stage65_read_only(): return {'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'no_task_registered':True}
def classify_local_console_shell_route(path, method='GET'):
    p=str(path).split('?')[0]; bad=method.upper()!='GET' or p in FORBIDDEN_ROUTES
    return {'path':p,'method':method.upper(),'forbidden':bad,'severity':'CRITICAL' if bad else 'INFO'}
def _warn_context(path='', generated=False):
    p=str(path).replace('\\','/').lower()
    return generated or p.startswith('docs/') or '/tests/' in p or 'test_' in p or any(x in p for x in ['stage55','stage56','stage57','stage58','stage59','stage60','stage61','stage62','stage63','stage64','stage65','local_console_shell'])
def classify_local_console_shell_marker(marker, path='', generated=False, executable=False):
    if marker in {'xtdata','xtquant.xtdata'}: return 'INFO'
    return 'CRITICAL' if executable or not _warn_context(path, generated) else 'WARN'
def scan_local_console_shell_asset_for_forbidden_markers(text, path='', generated=False, executable=False):
    return [{'marker':m,'severity':classify_local_console_shell_marker(m,path,generated,executable),'path':str(path)} for m in MARKERS if m in text]
def assert_no_xttrader_import(paths=None):
    hits=[]
    for base in paths or ['qmt_ai_trading/local_console','scripts/run_local_console_shell_review.py']:
        p=Path(base); files=[p] if p.is_file() else list(p.rglob('*.py')) if p.exists() else []
        for f in files:
            txt=f.read_text(encoding='utf-8')
            if re.search(r'from\s+.*xttrader|import\s+.*xttrader|XtQuantTrader', txt): hits.append(str(f))
    return hits
def assert_no_forbidden_shell_routes(routes): return [r for r in routes if classify_local_console_shell_route(getattr(r,'path',r)).get('forbidden')]
def assert_no_forbidden_js_actions(js): return [m for m in scan_local_console_shell_asset_for_forbidden_markers(js,'app.js',executable=True) if m['severity']=='CRITICAL']
