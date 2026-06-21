from __future__ import annotations
from dataclasses import dataclass
from .stage76_models import Stage76ReviewSeverity

FORBIDDEN_MARKERS=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post',"fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/approval')","fetch('/auto-approve')","fetch('/account')","fetch('/positions')","fetch('/assets')","fetch('/live')","fetch('/notify')","fetch('/execute')",'XMLHttpRequest','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','自动审批','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit']
@dataclass
class Stage76SafetyFinding:
    marker: str; path: str; severity: Stage76ReviewSeverity; context: str; note: str

def classify_marker(marker: str, path: str, context: str) -> Stage76ReviewSeverity:
    p=path.replace('\\','/').lower(); c=context.lower()
    if 'xtdata' in marker.lower() or 'xtquant.xtdata' in c: return Stage76ReviewSeverity.INFO
    if p.startswith('docs/') or p.startswith('tests/') or 'stage76_roadmap_review' in p: return Stage76ReviewSeverity.WARN
    if '不调用 xttrader' in context or 'not call xttrader' in c: return Stage76ReviewSeverity.INFO
    executable=any(p.endswith(x) for x in ['.py','.js','.ts','.tsx','.jsx','.ps1'])
    if executable and marker in FORBIDDEN_MARKERS: return Stage76ReviewSeverity.CRITICAL
    return Stage76ReviewSeverity.WARN

def scan_texts(texts: dict[str,str]) -> list[Stage76SafetyFinding]:
    out=[]
    for path,text in texts.items():
        for m in FORBIDDEN_MARKERS:
            if m in text:
                idx=text.find(m); ctx=text[max(0,idx-50):idx+80].replace('\n',' ')
                out.append(Stage76SafetyFinding(m,path,classify_marker(m,path,ctx),ctx,'Stage76 safety marker classification'))
    return out

def assert_read_only(read_only: bool, no_trade_authorization: bool) -> None:
    if not read_only or not no_trade_authorization:
        raise ValueError('Stage76 must remain read-only and no-trade-authorization')
