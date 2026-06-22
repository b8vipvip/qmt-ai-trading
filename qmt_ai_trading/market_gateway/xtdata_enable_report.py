from __future__ import annotations
import hashlib, json
from pathlib import Path
from .xtdata_enable_request import XtDataEnableRequest
from .xtdata_environment_check import run_environment_check
from .xtdata_manual_checklist import default_manual_checklist
from .xtdata_config_audit import audit_xtdata_config
from .xtdata_enable_decision import decide_xtdata_enable
STAGE='Stage86'
def write_json_if_changed(path,data):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); text=json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)
    if not p.exists() or p.read_text(encoding='utf-8')!=text: p.write_text(text,encoding='utf-8')
def write_text_if_changed(path,text):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists() or p.read_text(encoding='utf-8')!=text: p.write_text(text,encoding='utf-8')
def stable_stage_timestamp(stage,input_hash): return f'2026-01-01T00:00:00+00:00#{stage}-{input_hash[:12]}'
def md(title,data): return '# '+title+'\n\n```json\n'+json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n```\n'
def _load_json(root,rel):
    p=root/rel
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: return {'error':str(e),'path':rel}
def run_xtdata_enable_stage86(repo_root='.', output_dir='local_console_xtdata_enable_stage86', **overrides):
    root=Path(repo_root); out=root/output_dir
    inputs=['local_console_xtdata_stage85/xtdata_boundary_report.json','local_console_xtdata_stage85/xtdata_adapter_config.json','local_console_xtdata_stage85/xtdata_import_guard_report.json','local_console_xtdata_stage85/xtdata_capability_probe.json','local_console_xtdata_stage85/xtdata_safety_report.json','local_console_xtdata_stage85/frontend_xtdata_contract.json','local_console_xtdata_stage85/next_xtdata_sandbox_enable_plan.json','local_console_market_stage84/market_gateway_report.json','local_console_market_stage84/frontend_market_contract.json','local_console_monitoring_stage83/system_health_report.json','local_console_monitoring_stage83/circuit_breaker_status.json']
    loaded={rel:_load_json(root,rel) for rel in inputs}; missing=[k for k,v in loaded.items() if v is None]
    h=hashlib.sha256(json.dumps(loaded,ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest(); created=stable_stage_timestamp(STAGE,h)
    context={'stage':STAGE,'created_at':created,'input_files':inputs,'missing_inputs':missing,'fallback_used':bool(missing),'mock_data':True,'sandbox_only':True,'xtdata_enabled':False,'real_market_data':False,'not_live_trading':True,'read_only':True,'requires_human_confirmation':True}
    req_data=XtDataEnableRequest(created_at=created).to_dict(); req_data.update({k:v for k,v in overrides.items() if k in req_data}); request=XtDataEnableRequest(**req_data).to_dict()
    env=run_environment_check(root).to_dict(); checklist=default_manual_checklist().to_dict(); audit=audit_xtdata_config(loaded.get('local_console_xtdata_stage85/xtdata_adapter_config.json') or {}, request).to_dict(); decision=decide_xtdata_enable(checklist, env, audit, request); decision['created_at']=created; decision['stage']=STAGE
    report={'stage':STAGE,'created_at':created,'task_id':'xtdata_enable_dry_run','status':'SUCCESS','output_dir':output_dir,'report_path':f'{output_dir}/xtdata_enable_report.md','workflow':['Stage85 XtData Boundary Report','XtData Sandbox Enable Request','Environment Dry-run Check','Manual Confirmation Checklist','Config Audit','Safety Gate','Enable Decision','Frontend xtdata Enable Checklist'],'decision':decision['decision'],'enable_xtdata':False,'real_market_data':False,'mini_qmt_connected':False,'xtdata_imported':False,'dry_run':True,'read_only':True,'requires_human_review':True,'requires_human_confirmation':True,'manual_confirmation_completed':False,'allow_xttrader':False,'warnings':env.get('warnings',[])}
    frontend={'page':'xtdata 启用确认','apis':['GET /api/v1/market/xtdata-enable/context','GET /api/v1/market/xtdata-enable/request','GET /api/v1/market/xtdata-enable/environment','GET /api/v1/market/xtdata-enable/checklist','GET /api/v1/market/xtdata-enable/audit','GET /api/v1/market/xtdata-enable/decision','GET /api/v1/market/xtdata-enable/report','POST /api/v1/tasks/run task_id=xtdata_enable_dry_run'],'sections':['xtdata 启用请求状态','环境检测结果','人工确认 checklist','配置审计表','安全阻断原因','sandbox fallback 状态','下一阶段计划','安全边界说明'],'enable_xtdata':False,'real_market_data':False,'mini_qmt_connected':False,'xtdata_imported':False,'read_only':True,'dry_run':True,'requires_human_confirmation':True,'manual_confirmation_completed':False,'allow_xttrader':False,'decision':decision['decision'],'safety_boundary':'Stage86 only creates dry-run reports and cannot enable live data.'}
    plan={'stage':'Stage87','title':'xtdata Adapter Probe disabled-mode 联调','goals':['disabled-mode adapter probe','return disabled/blocked/dry-run only','no xtdata import','no MiniQMT connection','no xttrader','no account query']}
    files={'xtdata_enable_input_context':context,'xtdata_enable_request':request,'xtdata_environment_check':env,'xtdata_manual_checklist':checklist,'xtdata_config_audit':audit,'xtdata_enable_decision':decision,'xtdata_enable_report':report,'frontend_xtdata_enable_contract':frontend,'next_xtdata_adapter_probe_plan':plan}
    for n,d in files.items(): write_json_if_changed(out/f'{n}.json',d); write_text_if_changed(out/f'{n}.md',md(n,d))
    return report
