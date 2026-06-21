from __future__ import annotations
from .help_models import DocsSafetyFinding, LocalConsoleHelpSeverity
from .help_assets import FORBIDDEN_ROUTES
MOJIBAKE=['鏈','鍙','楠','涓','绛','璇','瀹','鐩','鎺','鏉','�','\x00']
DANGEROUS=['XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post',"fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/approval')","fetch('/auto-approve')","fetch('/account')","fetch('/positions')","fetch('/assets')","fetch('/live')","fetch('/notify')","fetch('/execute')",'XMLHttpRequest','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','自动审批','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit','tradeButton','approveButton','orderButton','liveButton','notifyButton','accountButton','positionButton','executeButton','submitOrder','approveOrder','sendNotification','autoApproveButton','liveApproveButton']

def assert_stage73_read_only(read_only=True,dry_run_only=True,no_trade_authorization=True):
    if not (read_only and dry_run_only and no_trade_authorization): raise ValueError('Stage73 must stay read_only/dry_run_only/no_trade_authorization')

def classify_help_hash_route(route): return LocalConsoleHelpSeverity.CRITICAL if route in FORBIDDEN_ROUTES else LocalConsoleHelpSeverity.INFO
def assert_no_forbidden_help_routes(routes):
    bad=[r for r in routes if classify_help_hash_route(r)==LocalConsoleHelpSeverity.CRITICAL]
    if bad: raise ValueError('forbidden help routes: '+','.join(bad))

def classify_help_marker(marker, context='', path=''):
    low=(context+' '+path).lower()
    if marker=='xttrader' and ('不调用 xttrader' in context or 'no xttrader' in low or 'safety-banner' in low or path.endswith(('.md','.json','.html'))): return LocalConsoleHelpSeverity.WARN
    if '不是审批授权' in context or '不是实盘授权' in context: return LocalConsoleHelpSeverity.INFO
    if marker in DANGEROUS or marker=='xttrader': return LocalConsoleHelpSeverity.CRITICAL
    return LocalConsoleHelpSeverity.WARN

def scan_help_assets_for_forbidden_markers(assets):
    findings=[]
    for path,text in assets.items():
        assert_no_mojibake_in_help_outputs(text)
        for marker in ['xttrader']+DANGEROUS:
            if marker in text:
                sev=classify_help_marker(marker,text,path)
                findings.append(DocsSafetyFinding(marker,path,sev,text[:180],'Stage73 marker classification'))
    return findings

def assert_no_forbidden_help_actions(js_text):
    executable_markers=[m for m in DANGEROUS if m not in {'自动批准','自动approve','自动审批','绕过风控','bypass Risk Gate','bypass Human Approval'}]
    bad=[m for m in executable_markers if m in js_text]
    if 'xttrader' in js_text and '不调用 xttrader' not in js_text: bad.append('xttrader')
    if bad: raise ValueError('forbidden frontend actions: '+','.join(bad))

def assert_no_xttrader_import(text=''):
    if 'XtQuantTrader' in text or 'import xttrader' in text: raise ValueError('xttrader import forbidden')
def assert_no_forbidden_help_frontend_actions(text=''): assert_no_forbidden_help_actions(text)
def assert_help_docs_are_not_approval(payload):
    s=str(payload)
    if '自动批准' in s or '自动审批' in s or 'auto approve' in s: raise ValueError('help docs must not be approval')
def assert_help_docs_are_not_trade_authorization(payload):
    s=str(payload)
    if '交易授权' in s and '不是交易授权' not in s: raise ValueError('help docs must not be trade authorization')
def assert_no_mojibake_in_help_outputs(text):
    if any(m in text for m in MOJIBAKE): raise ValueError('mojibake marker found')
