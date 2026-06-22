from __future__ import annotations
import json, re
from pathlib import Path
SAFETY={"read_only":True,"dry_run":True,"live_disabled":True,"no_order_submitted":True,"requires_human_approval":True,"account_masked":True,"order_submit_enabled":False,"order_cancel_enabled":False,"real_order_submitted":False}
CONSOLE=Path('artifacts/reports/console')
LEGACY={
 'datahub':['local_console_datahub_stage88'],'research':['local_console_research_stage88','local_console_factor_stage79'],'strategy':['local_console_strategy_stage88'], 'risk':['local_console_risk_stage88'],
 'agent':['local_console_agent_stage81'],'paper':['local_console_paper_stage89','local_console_backtest_stage82'],'monitoring':['local_console_monitoring_stage83'],'account_readonly':['local_console_account_stage91'],
 'market':['local_console_xtdata_live_stage87','local_console_xtdata_stage85','local_console_market_stage84'], 'workflow':['local_console_workflow_stage91','local_console_workflow_stage87']}
def mask(obj):
    if isinstance(obj, dict):
        out={}
        for k,v in obj.items():
            lk=k.lower()
            if any(s in lk for s in ['account_id','api_key','token','secret','password']): out[k]='***MASKED***'
            else: out[k]=mask(v)
        return out
    if isinstance(obj, list): return [mask(x) for x in obj]
    if isinstance(obj, str) and re.fullmatch(r'\d{6,}', obj): return obj[:2]+'***'+obj[-2:]
    return obj
def read_json(module,name,default):
    paths=[CONSOLE/module/name]+[Path(d)/name for d in LEGACY.get(module,[])]
    for p in paths:
        if p.exists():
            try: return mask(json.loads(p.read_text(encoding='utf-8')))
            except Exception as e: return {**SAFETY,'status':'DATA_ERROR','error':str(e),'source_path':str(p)}
    return {**SAFETY,'status':'DATA_MISSING','source_path':str(paths[0])}
def payload(**kw):
    out={"ok":True, **SAFETY, **kw}
    return mask(out)
