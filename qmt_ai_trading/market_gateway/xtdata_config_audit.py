from __future__ import annotations
from dataclasses import dataclass, asdict

SAFE_EXPECTED={'enabled':False,'allow_import_xtdata':False,'allow_connect_miniqmt':False,'allow_real_market_data':False,'allow_xttrader':False,'read_only':True,'dry_run':True,'sandbox_fallback':True}
DANGEROUS={'enabled':True,'allow_import_xtdata':True,'allow_connect_miniqmt':True,'allow_real_market_data':True,'allow_xttrader':True,'read_only':False,'dry_run':False}
@dataclass(frozen=True)
class XtDataConfigAudit:
    audit_status: str; safety_status: str; decision: str; requires_human_review: bool; findings: tuple; expected: dict
    def to_dict(self):
        d=asdict(self); d['findings']=list(self.findings); return d

def audit_xtdata_config(stage85_config=None, request=None):
    cfg=dict(stage85_config or {}); req=dict(request or {})
    vals={**cfg, **{'enabled': req.get('enable_xtdata', cfg.get('enabled', False)), 'allow_real_market_data': req.get('enable_real_market_data', cfg.get('allow_real_market_data', False)), 'allow_connect_miniqmt': req.get('connect_miniqmt', cfg.get('allow_connect_miniqmt', False)), 'allow_xttrader': req.get('allow_xttrader', cfg.get('allow_xttrader', False)), 'dry_run': req.get('dry_run', cfg.get('dry_run', True)), 'read_only': req.get('read_only', cfg.get('read_only', True)), 'sandbox_fallback': cfg.get('sandbox_fallback', True)}}
    findings=[]
    for k,bad in DANGEROUS.items():
        if vals.get(k) is bad: findings.append({'name':k,'value':vals.get(k),'status':'BLOCKED','message':'dangerous xtdata enable configuration'})
    status='BLOCKED' if findings else 'PASS'
    return XtDataConfigAudit(status,status,'BLOCKED' if findings else 'READY_FOR_MANUAL_REVIEW',True,tuple(findings),SAFE_EXPECTED)
