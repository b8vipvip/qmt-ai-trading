from __future__ import annotations
ALLOWED={'BLOCKED','READY_FOR_MANUAL_REVIEW','SANDBOX_ONLY'}
def decide_xtdata_enable(checklist, environment, audit, request):
    blocking=[]
    if audit.get('safety_status')=='BLOCKED': blocking += audit.get('findings',[])
    if not checklist.get('manual_confirmation_completed', False): blocking.append({'name':'manual_confirmation_completed','status':'REQUIRES_HUMAN_REVIEW'})
    decision='BLOCKED' if audit.get('safety_status')=='BLOCKED' else 'READY_FOR_MANUAL_REVIEW'
    assert decision in ALLOWED
    return {'decision':decision,'reason':'Stage86 is dry-run only; human checklist is not completed' if decision!='BLOCKED' else 'Dangerous xtdata enable configuration blocked','blocking_items':blocking,'manual_checklist_status':checklist.get('checklist_status','REQUIRES_HUMAN_REVIEW'),'environment_status':environment.get('environment_status','PASS'),'config_audit_status':audit.get('audit_status','PASS'),'dry_run':True,'read_only':True,'xtdata_enabled':False,'real_market_data':False,'mini_qmt_connected':False,'xtdata_imported':False,'requires_human_review':True}
