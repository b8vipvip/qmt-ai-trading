from __future__ import annotations
import json, re
from pathlib import Path
SAFETY={"read_only":True,"dry_run":True,"live_disabled":True,"no_order_submitted":True,"requires_human_approval":True,"account_masked":True,"order_submit_enabled":False,"order_cancel_enabled":False,"real_order_submitted":False,"live_trading_enabled":False,"allow_order_submit":False,"allow_order_cancel":False}
CONSOLE=Path('artifacts/reports/console')
def mask(obj):
    if isinstance(obj, dict):
        return {k:('***MASKED***' if any(s in k.lower() for s in ['account_id','api_key','token','secret','password']) else mask(v)) for k,v in obj.items()}
    if isinstance(obj, list): return [mask(x) for x in obj]
    if isinstance(obj, str) and re.fullmatch(r'\d{6,}', obj): return obj[:2]+'***'+obj[-2:]
    return obj
def read_json(module,name,default):
    p=CONSOLE/module/name
    if p.exists():
        try: return mask(json.loads(p.read_text(encoding='utf-8')))
        except Exception as e: return {**SAFETY,'status':'DATA_ERROR','error':str(e),'source_path':str(p)}
    return mask({**SAFETY,'status':'DATA_MISSING','empty_reason':'统一控制台产物不存在，请运行 scripts/refresh_console_artifacts.ps1','source_path':str(p), **(default if isinstance(default,dict) else {'items':default})})
def payload(**kw):
    out={"ok":True, **SAFETY, **kw}
    if out.get('ok') is False: out['ok']=False
    return mask(out)
