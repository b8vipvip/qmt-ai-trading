from __future__ import annotations
import ast
from pathlib import Path
from .acceptance_models import UiAcceptanceSafetyFinding, LocalConsoleAcceptanceSeverity

FORBIDDEN_ROUTES={'#/order','#/orders','#/trade','#/execute','#/approve','#/approval','#/auto-approve','#/live','#/notify','#/account','#/positions','#/assets'}
DANGEROUS_MARKERS=['XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post',"fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/approval')","fetch('/auto-approve')","fetch('/account')","fetch('/positions')","fetch('/assets')","fetch('/live')","fetch('/notify')","fetch('/execute')",'XMLHttpRequest','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','自动审批','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit','tradeButton','approveButton','orderButton','liveButton','notifyButton','accountButton','positionButton','executeButton','submitOrder','approveOrder','sendNotification','autoApproveButton','liveApproveButton']

def assert_stage72_read_only(read_only=True,dry_run_only=True,no_trade_authorization=True):
    if not (read_only and dry_run_only and no_trade_authorization): raise ValueError('Stage72 must remain read_only=True dry_run_only=True no_trade_authorization=True')

def classify_acceptance_hash_route(route): return LocalConsoleAcceptanceSeverity.CRITICAL if route in FORBIDDEN_ROUTES else LocalConsoleAcceptanceSeverity.INFO

def assert_no_forbidden_acceptance_routes(routes):
    bad=[r for r in routes if classify_acceptance_hash_route(r)==LocalConsoleAcceptanceSeverity.CRITICAL]
    if bad: raise ValueError(f'Forbidden Stage72 hash routes: {bad}')

def classify_acceptance_marker(marker, path='', context=''):
    low=(context or '').lower(); p=str(path).lower()
    if marker in ('xtdata','xtquant.xtdata'): return LocalConsoleAcceptanceSeverity.INFO
    if marker in ('xttrader','XtQuantTrader') and ('不调用' in context or '不得' in context or 'no ' in low or 'safety' in p or p.endswith(('.md','.json','.html'))): return LocalConsoleAcceptanceSeverity.WARN
    if '不是审批授权' in context or '不是交易授权' in context or '不提供' in context or '安全边界禁止' in context: return LocalConsoleAcceptanceSeverity.INFO
    if marker in DANGEROUS_MARKERS or marker in ('xttrader','XtQuantTrader'): return LocalConsoleAcceptanceSeverity.CRITICAL
    return LocalConsoleAcceptanceSeverity.WARN

def scan_acceptance_assets_for_forbidden_markers(assets):
    findings=[]
    for path,text in assets.items():
        for marker in ['xttrader','XtQuantTrader','xtdata','xtquant.xtdata']+DANGEROUS_MARKERS:
            if marker in text:
                sev=classify_acceptance_marker(marker,path,text[max(0,text.find(marker)-40):text.find(marker)+80])
                findings.append(UiAcceptanceSafetyFinding(marker,path,sev,text[max(0,text.find(marker)-60):text.find(marker)+120],'classified by Stage72 read-only safety scanner'))
    return findings

def assert_no_forbidden_acceptance_actions(js_text):
    critical=[f for f in scan_acceptance_assets_for_forbidden_markers({'app.js':js_text}) if f.severity==LocalConsoleAcceptanceSeverity.CRITICAL]
    if critical: raise ValueError(f'Forbidden Stage72 frontend actions: {critical}')

def assert_no_xttrader_import(py_text=''):
    tree=ast.parse(py_text or '')
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            names=[a.name for a in getattr(node,'names',[])] + ([node.module] if getattr(node,'module',None) else [])
            if any(n and ('xttrader' in n or 'XtQuantTrader' in n) for n in names): raise ValueError('Forbidden xttrader import')

def assert_no_forbidden_acceptance_frontend_actions(js_text=''): assert_no_forbidden_acceptance_actions(js_text)

def assert_acceptance_summary_is_not_approval(payload):
    text=str(payload).lower()
    if 'auto approve' in text or '自动批准' in text or '自动审批' in text: raise ValueError('Acceptance summary must not be approval')

def assert_acceptance_conclusion_is_not_trade_authorization(payload):
    text=str(payload).lower()
    if 'trade authorization granted' in text or '实盘授权通过' in text: raise ValueError('Conclusion draft must not be trade authorization')
