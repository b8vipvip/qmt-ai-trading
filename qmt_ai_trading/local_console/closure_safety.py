from __future__ import annotations
from .closure_models import UiProductizationClosureSafetyFinding, LocalConsoleClosureSeverity
from .closure_assets import FORBIDDEN_ROUTES
MOJIBAKE=['鏈','鍙','楠','涓','绛','璇','瀹','鐩','鎺','鏉','�','\x00']
DANGEROUS=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post',"fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/approval')","fetch('/auto-approve')","fetch('/account')","fetch('/positions')","fetch('/assets')","fetch('/live')","fetch('/notify')","fetch('/execute')",'XMLHttpRequest','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','自动审批','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit','tradeButton','approveButton','orderButton','liveButton','notifyButton','accountButton','positionButton','executeButton','submitOrder','approveOrder','sendNotification','autoApproveButton','liveApproveButton','.env','token','secret','credential','market_data','reports','logs','validation_logs']
def assert_stage75_read_only(read_only=True,dry_run_only=True,no_trade_authorization=True):
    if not (read_only and dry_run_only and no_trade_authorization): raise ValueError('Stage75 must stay read_only/dry_run_only/no_trade_authorization')
def classify_closure_hash_route(route): return LocalConsoleClosureSeverity.CRITICAL if route in FORBIDDEN_ROUTES else LocalConsoleClosureSeverity.INFO
def assert_no_forbidden_closure_routes(routes):
    bad=[r for r in routes if classify_closure_hash_route(r)==LocalConsoleClosureSeverity.CRITICAL]
    if bad: raise ValueError('forbidden closure routes: '+','.join(bad))
def classify_closure_marker(marker, context='', path=''):
    low=(context+' '+path).lower()
    if marker in {'xtdata','xtquant.xtdata'}: return LocalConsoleClosureSeverity.INFO
    if marker=='xttrader' and ('不调用 xttrader' in context or 'safety' in low or path.endswith(('.md','.json','.html'))): return LocalConsoleClosureSeverity.WARN
    if '不是审批授权' in context or '不是实盘授权' in context or '不提供交易/账户/审批/通知/自动批准功能' in context: return LocalConsoleClosureSeverity.INFO
    if path.endswith('.js') and marker in DANGEROUS: return LocalConsoleClosureSeverity.CRITICAL
    if marker in DANGEROUS: return LocalConsoleClosureSeverity.CRITICAL
    return LocalConsoleClosureSeverity.WARN
def scan_closure_assets_for_forbidden_markers(assets):
    findings=[]
    for path,text in assets.items():
        assert_no_mojibake_in_closure_outputs(text)
        for marker in DANGEROUS:
            if marker in text:
                findings.append(UiProductizationClosureSafetyFinding(marker,path,classify_closure_marker(marker,text,path),text[:180],'Stage75 marker classification'))
    return findings
def assert_no_forbidden_closure_actions(js_text):
    bad=[m for m in DANGEROUS if m in js_text and not (m=='xttrader' and '不调用 xttrader' in js_text) and not ('不提供交易/账户/审批/通知/自动批准功能' in js_text and m=='自动批准')]
    if bad: raise ValueError('forbidden frontend actions: '+','.join(bad))
def assert_no_xttrader_import(text=''):
    if 'XtQuantTrader' in text or 'import xttrader' in text: raise ValueError('xttrader import forbidden')
def assert_no_forbidden_closure_frontend_actions(text=''): assert_no_forbidden_closure_actions(text)
def assert_closure_package_is_not_approval(payload):
    s=str(payload)
    if ('审批授权' in s and '不是审批授权' not in s) or '自动审批能力' in s: raise ValueError('closure package must not be approval')
def assert_closure_package_is_not_trade_authorization(payload):
    s=str(payload)
    if '交易授权' in s and '不是交易授权' not in s: raise ValueError('closure package must not be trade authorization')
def assert_final_conclusion_is_not_approval(payload): assert_closure_package_is_not_approval(payload)
def assert_no_mojibake_in_closure_outputs(text):
    if any(m in text for m in MOJIBAKE): raise ValueError('mojibake marker found')
def assert_no_sensitive_closure_sources(sources):
    bad=[s for s in sources if any(m in str(s) for m in ['.env','token','secret','credential','market_data','reports','logs','validation_logs'])]
    if bad: raise ValueError('sensitive closure sources: '+','.join(map(str,bad)))
