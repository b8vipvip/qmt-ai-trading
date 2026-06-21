from __future__ import annotations
from pathlib import Path
from .review_models import ReviewSafetyFinding, LocalConsoleReviewSeverity

ALLOWED_HASH_ROUTES = ['#/dashboard','#/reports','#/reports/detail','#/reports/preview','#/reports/export','#/review-workbench','#/review-checklist','#/review-notes','#/review-package','#/local-confirmations','#/filters','#/warnings','#/blocking-reasons','#/manifest','#/validation','#/scheduler','#/safety','#/api','#/next']
FORBIDDEN_HASH_ROUTES = ['#/order','#/orders','#/trade','#/execute','#/approve','#/approval','#/auto-approve','#/live','#/notify','#/account','#/positions','#/assets']
DANGEROUS_MARKERS = ['XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','requests.post','XMLHttpRequest','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit','tradeButton','approveButton','orderButton','liveButton','notifyButton','accountButton','positionButton','executeButton','submitOrder','approveOrder','sendNotification','autoApproveButton','liveApproveButton']
FORBIDDEN_FETCHES = ["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/approval')","fetch('/auto-approve')","fetch('/account')","fetch('/positions')","fetch('/assets')","fetch('/live')","fetch('/notify')","fetch('/execute')"]
SENSITIVE = ['.env','token','key','secret','credential']
SENSITIVE_DIRS = ['market_data','reports','logs','validation_logs']
ALLOWED_EXPORT_EXTENSIONS = {'.md', '.json', '.html', '.css', '.js'}
ALLOWED_EXPORT_ROOT = 'local_console_review_stage71'
FORBIDDEN_EXPORT_PAYLOAD_MARKERS = [
    '.env', 'token', 'api_key', 'secret', 'credential',
    'market_data', 'reports', 'logs', 'validation_logs',
    'account_id', 'account_no', 'position_detail', 'order_detail', 'trade_detail',
    '资金', '持仓', '订单', '成交',
    '../', '..\\', 'xttrader', 'XtQuantTrader',
]

def assert_stage71_read_only(read_only=True,dry_run_only=True,no_trade_authorization=True):
    if not (read_only and dry_run_only and no_trade_authorization):
        raise ValueError('Stage71 must remain read_only=True dry_run_only=True no_trade_authorization=True')

def classify_review_hash_route(route: str) -> LocalConsoleReviewSeverity:
    return LocalConsoleReviewSeverity.CRITICAL if route in FORBIDDEN_HASH_ROUTES else LocalConsoleReviewSeverity.INFO

def assert_no_forbidden_review_routes(routes):
    bad=[r for r in routes if classify_review_hash_route(r)==LocalConsoleReviewSeverity.CRITICAL]
    if bad: raise ValueError(f'Forbidden Stage71 hash routes: {bad}')

def classify_review_marker(marker: str, path: str='', context: str='', generated: bool=False) -> LocalConsoleReviewSeverity:
    text=f'{path} {context}'.lower()
    m=marker.lower()
    if m in ('xtdata','xtquant.xtdata'): return LocalConsoleReviewSeverity.INFO
    if '不调用 xttrader' in context or 'safety banner' in text or generated or any(x in text for x in ['docs/','generated','data_bundle','static_safety','next plan']):
        return LocalConsoleReviewSeverity.WARN if 'xttrader' in m or marker in DANGEROUS_MARKERS else LocalConsoleReviewSeverity.INFO
    if marker in FORBIDDEN_FETCHES or marker in DANGEROUS_MARKERS or m == 'xttrader': return LocalConsoleReviewSeverity.CRITICAL
    if any(x in m for x in ['../','.env','token','secret','credential']): return LocalConsoleReviewSeverity.CRITICAL
    return LocalConsoleReviewSeverity.INFO

def scan_review_assets_for_forbidden_markers(assets: dict[str,str], generated: bool=False):
    markers=['xttrader']+DANGEROUS_MARKERS+FORBIDDEN_FETCHES+['../','.env','token','secret','credential']
    findings=[]
    for path,text in assets.items():
        for marker in markers:
            if marker in text:
                if marker == '自动批准' and '不提供交易/账户/审批/通知/自动批准功能' in text:
                    continue
                sev=classify_review_marker(marker,path,text,generated=generated and path!='app.js')
                findings.append(ReviewSafetyFinding(marker,path,sev,text[:240],'classified by Stage71 read-only safety scanner'))
    return findings

def assert_no_forbidden_review_actions(js_text: str):
    critical=[]
    safe_text=js_text.replace('该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。','')
    for marker in DANGEROUS_MARKERS+FORBIDDEN_FETCHES:
        if marker in safe_text: critical.append(marker)
    if critical: raise ValueError(f'Forbidden Stage71 frontend actions: {critical}')

def assert_no_xttrader_import(paths=None):
    paths=paths or []
    for p in paths:
        text=Path(p).read_text(encoding='utf-8') if Path(p).exists() else ''
        if 'XtQuantTrader' in text or 'xtquant.xttrader' in text:
            raise ValueError(f'Forbidden xttrader import in {p}')

def assert_no_forbidden_review_frontend_actions(js_text=''):
    return assert_no_forbidden_review_actions(js_text)

def _normalize_export_path_text(path) -> str:
    return str(path).strip().replace('\\', '/')

def _export_path_segments(normalized: str) -> list[str]:
    return [part for part in normalized.split('/') if part]

def assert_export_path_is_safe(path):
    s = _normalize_export_path_text(path)
    lower = s.lower()
    if not s:
        raise ValueError('Unsafe export path: empty path')
    if s.startswith('~'):
        raise ValueError(f'Unsafe export path: {path}')
    if s.startswith('/') or s.startswith('\\'):
        raise ValueError(f'Unsafe export path: {path}')
    if len(s) >= 2 and s[1] == ':' and s[0].isalpha():
        raise ValueError(f'Unsafe export path: {path}')
    parts = _export_path_segments(s)
    if not parts or any(part in {'.', '..'} for part in parts):
        raise ValueError(f'Unsafe export path: {path}')
    if any(marker in lower for marker in SENSITIVE):
        raise ValueError(f'Unsafe export path: {path}')
    if any(part.lower() in SENSITIVE_DIRS for part in parts):
        raise ValueError(f'Unsafe export path: {path}')
    if len(parts) > 1 and parts[0] != ALLOWED_EXPORT_ROOT:
        raise ValueError(f'Unsafe export path outside {ALLOWED_EXPORT_ROOT}: {path}')
    suffix = Path(parts[-1]).suffix.lower()
    if suffix not in ALLOWED_EXPORT_EXTENSIONS:
        raise ValueError(f'Unsafe export extension: {path}')

def _walk_export_payload(value):
    if isinstance(value, dict):
        for k, v in value.items():
            yield str(k)
            yield from _walk_export_payload(v)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _walk_export_payload(item)
    else:
        yield str(value)

def assert_export_payload_is_safe(payload):
    chunks = [chunk for chunk in _walk_export_payload(payload)]
    text = ' '.join(chunks).lower()
    unsafe = [m for m in FORBIDDEN_EXPORT_PAYLOAD_MARKERS if m.lower() in text]
    if unsafe:
        raise ValueError(f'Unsafe export payload contains forbidden marker: {unsafe[0]}')
    if isinstance(payload, dict):
        required = {
            'read_only': True,
            'dry_run_only': True,
            'no_trade_authorization': True,
        }
        for key, expected in required.items():
            if payload.get(key) is not expected:
                raise ValueError(f'Unsafe export payload missing {key}=True')
        note = str(payload.get('note') or payload.get('summary') or '')
        if '不是交易授权' not in note and '不是实盘授权' not in note and 'not trade authorization' not in note.lower():
            raise ValueError('Unsafe export payload must state it is not trade authorization')

def assert_no_sensitive_export_sources(sources):
    bad=[]
    for src in sources:
        try:
            assert_export_path_is_safe(src)
        except ValueError:
            bad.append(src)
            continue
        s=str(src).replace('\\','/').lower()
        parts=[p for p in s.split('/') if p]
        if any(x in s for x in SENSITIVE) or any(d in parts for d in SENSITIVE_DIRS): bad.append(src)
    if bad: raise ValueError(f'Sensitive export sources: {bad}')


def assert_review_notes_are_not_approval(payload):
    text=str(payload).lower()
    if 'auto approve' in text or '自动批准' in text or '自动审批动作' in text:
        raise ValueError('Review notes must not be an approval action')
    return True

def assert_checklist_is_not_trade_authorization(payload):
    text=str(payload).lower()
    if 'trade authorization=true' in text or '交易授权=true' in text or 'real_order_enabled=true' in text:
        raise ValueError('Checklist must not be trade authorization')
    return True
