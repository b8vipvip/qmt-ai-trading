from __future__ import annotations
from pathlib import Path
from .drilldown_models import ExportSafetyFinding, LocalConsoleDrilldownSeverity

ALLOWED_HASH_ROUTES = ['#/dashboard','#/reports','#/reports/detail','#/reports/preview','#/reports/export','#/filters','#/warnings','#/blocking-reasons','#/manifest','#/validation','#/scheduler','#/safety','#/api','#/review-package','#/next']
FORBIDDEN_HASH_ROUTES = ['#/order','#/orders','#/trade','#/execute','#/approve','#/live','#/notify','#/account','#/positions','#/assets']
DANGEROUS_MARKERS = ['XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','requests.post','XMLHttpRequest','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit','tradeButton','approveButton','orderButton','liveButton','notifyButton','accountButton','positionButton','executeButton','submitOrder','approveOrder','sendNotification']
FORBIDDEN_FETCHES = ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","fetch('/positions')","fetch('/assets')","fetch('/live')","fetch('/notify')","fetch('/execute')"]
SENSITIVE = ['.env','token','key','secret','credential']
SENSITIVE_DIRS = ['market_data','reports','logs','validation_logs']

def assert_stage70_read_only(read_only=True,dry_run_only=True,no_trade_authorization=True):
    if not (read_only and dry_run_only and no_trade_authorization):
        raise ValueError('Stage70 must remain read_only=True dry_run_only=True no_trade_authorization=True')

def classify_drilldown_hash_route(route: str) -> LocalConsoleDrilldownSeverity:
    return LocalConsoleDrilldownSeverity.CRITICAL if route in FORBIDDEN_HASH_ROUTES else LocalConsoleDrilldownSeverity.INFO

def assert_no_forbidden_drilldown_routes(routes):
    bad=[r for r in routes if classify_drilldown_hash_route(r)==LocalConsoleDrilldownSeverity.CRITICAL]
    if bad: raise ValueError(f'Forbidden Stage70 hash routes: {bad}')

def classify_drilldown_marker(marker: str, path: str='', context: str='', generated: bool=False) -> LocalConsoleDrilldownSeverity:
    text=f'{path} {context}'.lower()
    m=marker.lower()
    if m in ('xtdata','xtquant.xtdata'): return LocalConsoleDrilldownSeverity.INFO
    if '不调用 xttrader' in context or 'safety banner' in text or generated or any(x in text for x in ['docs/','generated','data_bundle','static_safety','next plan']):
        return LocalConsoleDrilldownSeverity.WARN if 'xttrader' in m or marker in DANGEROUS_MARKERS else LocalConsoleDrilldownSeverity.INFO
    if marker in FORBIDDEN_FETCHES or marker in DANGEROUS_MARKERS or m == 'xttrader': return LocalConsoleDrilldownSeverity.CRITICAL
    if any(x in m for x in ['../','.env','token','secret','credential']): return LocalConsoleDrilldownSeverity.CRITICAL
    return LocalConsoleDrilldownSeverity.INFO

def scan_drilldown_assets_for_forbidden_markers(assets: dict[str,str], generated: bool=False):
    markers=['xttrader']+DANGEROUS_MARKERS+FORBIDDEN_FETCHES+['../','.env','token','secret','credential']
    findings=[]
    for path,text in assets.items():
        for marker in markers:
            if marker in text:
                sev=classify_drilldown_marker(marker,path,text[:240],generated=generated and path!='app.js')
                findings.append(ExportSafetyFinding(marker,path,sev,text[:240],'classified by Stage70 read-only safety scanner'))
    return findings

def assert_no_forbidden_drilldown_actions(js_text: str):
    critical=[]
    for marker in DANGEROUS_MARKERS+FORBIDDEN_FETCHES:
        if marker in js_text: critical.append(marker)
    if critical: raise ValueError(f'Forbidden Stage70 frontend actions: {critical}')

def assert_no_xttrader_import(paths=None):
    paths=paths or []
    for p in paths:
        text=Path(p).read_text(encoding='utf-8') if Path(p).exists() else ''
        if 'XtQuantTrader' in text or 'xtquant.xttrader' in text:
            raise ValueError(f'Forbidden xttrader import in {p}')

def assert_no_forbidden_drilldown_frontend_actions(js_text=''):
    return assert_no_forbidden_drilldown_actions(js_text)

def assert_export_path_is_safe(path):
    p=Path(str(path))
    s=str(path).replace('\\','/')
    if p.is_absolute() or '../' in s or s.startswith('..') or any(x in s.lower() for x in SENSITIVE):
        raise ValueError(f'Unsafe export path: {path}')

def assert_export_payload_is_safe(payload):
    text=str(payload).lower()
    if any(x in text for x in ['.env','token','secret','credential']):
        raise ValueError('Unsafe export payload contains sensitive marker')

def assert_no_sensitive_export_sources(sources):
    bad=[]
    for src in sources:
        s=str(src).replace('\\','/').lower()
        parts=[p for p in s.split('/') if p]
        if any(x in s for x in SENSITIVE) or any(d in parts for d in SENSITIVE_DIRS): bad.append(src)
    if bad: raise ValueError(f'Sensitive export sources: {bad}')
