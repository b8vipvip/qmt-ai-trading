from __future__ import annotations
import json
from pathlib import Path
from .input_loader import load_context
from .anomaly_detector import detect_alerts
from .circuit_breaker import CircuitBreakerSimulator

def write_json_if_changed(path, data):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    text=json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)+"\n"
    if not path.exists() or path.read_text(encoding='utf-8')!=text: path.write_text(text, encoding='utf-8')
def write_text_if_changed(path, text):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith('\n'): text+='\n'
    if not path.exists() or path.read_text(encoding='utf-8')!=text: path.write_text(text, encoding='utf-8')
def md(title, obj): return f"# {title}\n\n```json\n{json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)}\n```\n"
def run_monitoring_stage83(repo_root='.', output_dir='local_console_monitoring_stage83'):
    out=Path(repo_root)/output_dir; ctx=load_context(repo_root); alerts=detect_alerts(ctx); cb=CircuitBreakerSimulator().evaluate(alerts, ctx)
    timeline=[{'event_id':f'EVT-{i+1:03d}','created_at':a['created_at'],'severity':a['severity'],'rule_id':a['rule_id'],'source_stage':a['source_stage'],'source_file':a['source_file'],'message':a['message'],'dry_run':True} for i,a in enumerate(alerts)]
    counts={s:sum(1 for a in alerts if a['severity']==s) for s in ['INFO','WARNING','HIGH','CRITICAL']}
    health={'stage':'Stage83','created_at':ctx['created_at'],'status':'ATTENTION' if alerts else 'HEALTHY','alert_count':len(alerts),'critical_count':counts['CRITICAL'],'warning_count':counts['WARNING'],'input_file_count':len(ctx['input_sources']),'missing_input_count':len(ctx['missing_files']),'fallback_used':ctx['fallback_used'],'mock_data':ctx['mock_data'],'repo_dirty':ctx['repo_dirty'],'validation_log_has_nul':bool(ctx['validation_nul_logs']),'dry_run':True,'not_live_trading':True,'research_only':True,'no_real_notification':True,'no_qmt_trader_api':True,'no_order_submitted':True,'requires_human_review':True}
    contract={'page':'监控告警','apis':['GET /api/v1/monitoring/context','GET /api/v1/monitoring/alerts/latest','GET /api/v1/monitoring/circuit-breaker/latest','GET /api/v1/monitoring/risk-events/latest','GET /api/v1/monitoring/system-health/latest','GET /api/v1/monitoring/report/latest','POST /api/v1/tasks/run task_id=monitoring_alert_dry_run'],'sections':['系统健康总览','告警数量统计','告警列表','严重级别筛选','熔断状态卡片','风险事件时间线','输入数据源状态','最近一次验证日志状态','禁止项检查结果','安全边界说明'],'dry_run':True,'not_live_trading':True,'research_only':True,'no_real_notification':True,'no_qmt_trader_api':True,'no_order_submitted':True,'requires_human_review':True,'forbidden_ui_policy':'前端不展示任何真实通知、自动交易、实盘授权或风控绕行入口文案'}
    plan={'stage':'Stage84','title':'真实行情接入前的 Sandbox 数据网关与回放总线','goals':['sandbox market data gateway','录制/模拟行情回放','真实 xtdata 接口边界','不接真实交易','不调用 xttrader','不查询真实账户'],'dry_run':True,'not_live_trading':True,'research_only':True}
    report={'stage':'Stage83','created_at':ctx['created_at'],'output_dir':output_dir,'report_path':f'{output_dir}/system_health_report.md','alert_count':len(alerts),'critical_count':counts['CRITICAL'],'circuit_breaker_status':cb['status'],'dry_run':True,'not_live_trading':True,'research_only':True,'no_real_notification':True,'warnings':[a['message'] for a in alerts if a['severity'] in {'WARNING','HIGH','CRITICAL'}]}
    files={'monitoring_input_context':ctx,'monitoring_alerts':{'alerts':alerts,'alert_count':len(alerts),'severity_counts':counts,'dry_run':True,'not_live_trading':True,'research_only':True,'no_real_notification':True},'circuit_breaker_status':cb,'risk_event_timeline':{'events':timeline,'dry_run':True,'not_live_trading':True,'research_only':True},'system_health_report':health,'frontend_monitoring_contract':contract,'next_live_sandbox_plan':plan}
    for name,obj in files.items(): write_json_if_changed(out/f'{name}.json', obj); write_text_if_changed(out/f'{name}.md', md(name, obj))
    return report
