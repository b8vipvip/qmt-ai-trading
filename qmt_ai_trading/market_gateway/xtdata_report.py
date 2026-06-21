from __future__ import annotations
import hashlib, json
from pathlib import Path
from .xtdata_adapter import XtDataAdapterBoundary
from .xtdata_config import XtDataAdapterConfig
from .xtdata_safety import scan_import_guard, evaluate_xtdata_safety

STAGE = "Stage85"

def write_json_if_changed(path, data):
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    text=json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    if not p.exists() or p.read_text(encoding='utf-8') != text:
        p.write_text(text, encoding='utf-8')

def write_text_if_changed(path, text):
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or p.read_text(encoding='utf-8') != text:
        p.write_text(text, encoding='utf-8')

def stable_stage_timestamp(stage, input_hash):
    return f"2026-01-01T00:00:00+00:00#{stage}-{input_hash[:12]}"

def md(title, data):
    return '# '+title+'\n\n```json\n'+json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)+'\n```\n'

def _load_json(root: Path, rel: str):
    p = root / rel
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception as exc:
        return {"error": str(exc), "path": rel}

def run_xtdata_boundary_stage85(repo_root='.', output_dir='local_console_xtdata_stage85', **overrides):
    root=Path(repo_root); out=root/output_dir
    input_files=[
        'local_console_market_stage84/market_gateway_report.json','local_console_market_stage84/frontend_market_contract.json','local_console_market_stage84/next_qmt_xtdata_boundary_plan.json',
        'local_console_monitoring_stage83/system_health_report.json','local_console_monitoring_stage83/monitoring_alerts.json','local_console_monitoring_stage83/circuit_breaker_status.json']
    loaded={rel:_load_json(root, rel) for rel in input_files}
    fallback_used=any(v is None for v in loaded.values())
    input_hash=hashlib.sha256(json.dumps(loaded, ensure_ascii=False, sort_keys=True, default=str).encode('utf-8')).hexdigest()
    created_at=stable_stage_timestamp(STAGE, input_hash)
    cfg_data = XtDataAdapterConfig().to_dict(); cfg_data.update({k:v for k,v in overrides.items() if k in cfg_data})
    cfg = XtDataAdapterConfig(**cfg_data)
    adapter = XtDataAdapterBoundary(cfg)
    import_guard = scan_import_guard([root/'qmt_ai_trading'/'market_gateway', root/'scripts'/'run_xtdata_boundary_stage85.py'])
    safety = evaluate_xtdata_safety(cfg)
    probe = {"config_check": adapter.check_config(), "import_probe": adapter.probe_import(), "connection_probe": adapter.probe_connection(), "snapshot_probe": adapter.get_snapshot(['510300.SH']), "bars_probe": adapter.get_bars('510300.SH','1d',5), "subscribe_probe": adapter.subscribe(['510300.SH'])}
    context={"stage":STAGE,"created_at":created_at,"input_files":input_files,"missing_inputs":[k for k,v in loaded.items() if v is None],"fallback_used":fallback_used,"mock_data":True,"sandbox_only":True,"xtdata_enabled":False,"real_market_data":False,"not_live_trading":True,"read_only":True,"no_order_submitted":True,"no_qmt_trader_api":True}
    config_report={"stage":STAGE,"created_at":created_at,**cfg.to_dict(),"xtdata_imported":False,"mini_qmt_connected":False,"real_market_data":False}
    capability={"stage":STAGE,"created_at":created_at,"status":"DISABLED","enabled":cfg.enabled,"dry_run":cfg.dry_run,"read_only":cfg.read_only,"xtdata_imported":False,"mini_qmt_connected":False,"real_market_data":False,"sandbox_fallback":cfg.sandbox_fallback,"probes":probe,"warnings":["Stage85 performs configuration-only dry-run probes."]}
    import_guard.update({"stage":STAGE,"created_at":created_at})
    safety.update({"stage":STAGE,"created_at":created_at})
    report={"stage":STAGE,"created_at":created_at,"task_id":"xtdata_boundary_dry_run","status":"SUCCESS","output_dir":output_dir,"report_path":f"{output_dir}/xtdata_boundary_report.md","enabled":cfg.enabled,"dry_run":cfg.dry_run,"read_only":cfg.read_only,"xtdata_imported":False,"mini_qmt_connected":False,"real_market_data":False,"sandbox_fallback":cfg.sandbox_fallback,"safety_status":safety['safety_status'],"warnings":capability['warnings'],"no_order_submitted":True,"no_qmt_trader_api":True,"workflow":["Stage84 Sandbox Market Gateway","XtData Adapter Config","Import Guard","Capability Probe Dry-run","Safety Gate","XtData Boundary Report","Frontend xtdata Boundary Checklist"]}
    frontend={"page":"xtdata 边界检查","apis":["GET /api/v1/market/xtdata/context","GET /api/v1/market/xtdata/config","GET /api/v1/market/xtdata/import-guard","GET /api/v1/market/xtdata/capability-probe","GET /api/v1/market/xtdata/safety","GET /api/v1/market/xtdata/report","POST /api/v1/tasks/run task_id=xtdata_boundary_dry_run"],"sections":["xtdata adapter 当前状态","配置开关表","Import Guard 检查结果","MiniQMT 连接状态 dry-run","真实行情权限 dry-run","Sandbox fallback 状态","Safety Gate 结果","下一阶段启用清单","安全边界说明"],"enabled":False,"dry_run":True,"read_only":True,"xtdata_imported":False,"mini_qmt_connected":False,"real_market_data":False,"sandbox_fallback":True,"allow_xttrader":False,"no_order_submitted":True,"no_qmt_trader_api":True}
    plan={"stage":"Stage86","title":"xtdata sandbox enable 开关与人工确认流程","still_disabled_by_default":True,"no_real_market_connection":True,"no_qmt_trader_api":True,"no_order_submitted":True,"checklist":["人工确认 checklist","环境检测","配置审计","继续 dry-run/read-only"]}
    files={"xtdata_input_context":context,"xtdata_adapter_config":config_report,"xtdata_import_guard_report":import_guard,"xtdata_capability_probe":capability,"xtdata_safety_report":safety,"xtdata_boundary_report":report,"frontend_xtdata_contract":frontend,"next_xtdata_sandbox_enable_plan":plan}
    for name,data in files.items():
        write_json_if_changed(out/f'{name}.json', data); write_text_if_changed(out/f'{name}.md', md(name, data))
    return report
