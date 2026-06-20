from __future__ import annotations
from pathlib import Path
from .models import LiveGrayReadonlySealSeverity
FORBIDDEN=['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit']
GENERATED_CONTEXTS=('qmt_dryrun_calibration_stage55/','real_cache_quality_stage56/','live_gray_candidate_stage57/','live_gray_final_approval_stage58/','live_gray_readonly_seal_stage59/','docs/','tests/','validation_logs/')
SAFETY_HINTS=('不调用','禁止调用','不真实下单','不查询真实账户','不查询资金','不查询持仓','不查询订单','不查询成交','不是实盘授权','不代表实盘授权','generated markdown','generated json','safety marker definitions','只表示')
EXEC_DANGER={x.lower() for x in ['xttrader','XtQuantTrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','requests.post','smtp','sendMessage','webhook','--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True']}
EXEC_SUFFIXES=('.py','.ps1','.yaml','.yml')
def classify_live_gray_readonly_seal_marker(marker: str, context: str='', text: str='')->LiveGrayReadonlySealSeverity:
    ctx=str(context).replace('\\','/').lower(); ml=str(marker).lower(); tl=str(text).lower()
    if 'xtdata' in ml and ml not in ('xttrader','xtquanttrader'): return LiveGrayReadonlySealSeverity.WARN
    if any(part in ctx for part in GENERATED_CONTEXTS): return LiveGrayReadonlySealSeverity.WARN
    if any(h in text or h in tl for h in SAFETY_HINTS): return LiveGrayReadonlySealSeverity.WARN
    if (ctx.endswith(EXEC_SUFFIXES) or context in ('','actual executable')) and ml in EXEC_DANGER: return LiveGrayReadonlySealSeverity.CRITICAL
    return LiveGrayReadonlySealSeverity.WARN
def scan_live_gray_readonly_seal_text_for_forbidden_markers(text: str, context: str='')->list[dict[str,str]]:
    return [{'marker':m,'severity':classify_live_gray_readonly_seal_marker(m,context,text).value,'context':context} for m in FORBIDDEN if m in text]
def assert_stage59_read_only(text: str='', context: str='actual executable')->None:
    bad=[f for f in scan_live_gray_readonly_seal_text_for_forbidden_markers(text,context) if f['severity']=='CRITICAL']
    if bad: raise RuntimeError('Stage59 read-only boundary violation: '+', '.join(f['marker'] for f in bad))
def assert_no_xttrader_import(path: str|Path)->None:
    p=Path(path); files=[p] if p.is_file() else [x for x in p.rglob('*.py') if '__pycache__' not in x.parts and 'live_gray_readonly_seal/safety.py' not in str(x).replace('\\','/')]
    bad=[]
    for f in files:
        txt=f.read_text(encoding='utf-8',errors='ignore')
        if 'xttrader' in txt or 'XtQuantTrader' in txt: bad.append(str(f))
    if bad: raise RuntimeError('xttrader import/call marker found: '+', '.join(bad))
