from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

STAGE='Stage87'
SAFETY={'dry_run':True,'read_only':True,'not_live_trading':True,'no_order_submitted':True,'no_xttrader':True,'no_account_query':True}

def _now(): return datetime.now(timezone.utc).isoformat()
def _exists(p): return Path(p).exists()

def _layer(name,status,api_status,source,report,interactive,backend_missing,next_action,safety):
    return {'layer':name,'module':name,'status':status,'api_status':api_status,'data_source':source,'data_source_path':source,'report_path':report,'last_run_time':_now() if _exists(report) else None,'interactive':interactive,'backend_missing':backend_missing,'read_only':True,'dry_run':True,'not_live_trading':True,'no_order_submitted':True,'safety_boundary':safety,'next_action':next_action}

def workflow_status(repo_root='.'):
    root=Path(repo_root)
    wf=[
      _layer('QMT Gateway / xtdata','INTERACTIVE','READY','xtdata_live_or_sandbox','local_console_xtdata_live_stage87/xtdata_live_report.json',True,False,'Run xtdata readonly smoke test','xtdata only; xttrader/account/order disabled'),
      _layer('Data Hub','BACKEND_MISSING','BACKEND_MISSING','data/cache/datahub; local parquet/duckdb/sqlite planned','local_console_workflow_stage87/workflow_status.json',False,True,'后端待开发，需要新增 Data Hub read-only status and cache API','read-only cache/status only; no trading'),
      _layer('Research / Qlib factors','INTERACTIVE','READY','local_console_factor_stage79/*.json','local_console_factor_stage79/factor_report.json',True,False,'Run factor_research_dry_run','Research only; no order path'),
      _layer('TradingAgents','INTERACTIVE','READY','local_console_agent_stage81/*.json','local_console_agent_stage81/agent_research_report.json',True,False,'Run agent_research_dry_run','Agent analysis only; no direct order'),
      _layer('Strategy Engine','INTERACTIVE','READY','task-store factor_strategy_dry_run','local_console_factor_stage80/strategy_report.json',True,False,'Run factor_strategy_dry_run and send TradeIntent to Risk Gate dry-run','Generates TradeIntent only; no live submit'),
      _layer('Risk Gate','INTERACTIVE','READY','risk dry-run decisions','local_console_workflow_stage87/workflow_dry_run_check.json',True,False,'Run risk_gate_dry_run','Risk rejection must include reasons; no bypass'),
      _layer('Human Approval','BACKEND_MISSING','BACKEND_MISSING','approval CLI/store planned','local_console_workflow_stage87/workflow_status.json',False,True,'后端待开发，需要新增 approval read-only API','No approve action in console; review only'),
      _layer('Paper Trading / Shadow Trading','BACKEND_MISSING','BACKEND_MISSING','paper/shadow stores planned','local_console_workflow_stage87/workflow_status.json',False,True,'后端待开发，需要新增 paper-trading and shadow-trading read-only API','Paper/shadow only; no live order'),
      _layer('Live Trading','DISABLED','READY','live trading disabled by default','local_console_workflow_stage87/workflow_status.json',False,False,'Keep disabled until explicit human approval and risk signoff','DISABLED_FOR_SAFETY; allow_xttrader=false; allow_order_submit=false'),
    ]
    return {'stage':STAGE,'workflow':wf,**SAFETY}

FEATURES=[
('QMT Gateway / xtdata','INTERACTIVE','/api/v1/market/xtdata-live/status','readonly xtdata smoke'),
('QMT Gateway / xttrader account query','DISABLED_FOR_SAFETY',None,'xttrader/account query forbidden'),
('QMT Gateway / order submit','DISABLED_FOR_SAFETY',None,'order submit forbidden'),
('Data Hub / symbols','BACKEND_MISSING','/api/v1/datahub/symbols','needs readonly API'),
('Data Hub / market cache','BACKEND_MISSING','/api/v1/datahub/cache/status','needs cache API'),
('Data Hub / ETF universe','READY',None,'python datahub ETF universe exists; API pending'),
('Research / factors','INTERACTIVE','/api/v1/factor/context','factor dry-run API'),
('Research / model lab','STATIC_PLACEHOLDER',None,'model lab UI/API pending'),
('TradingAgents / technical','INTERACTIVE','/api/v1/agents/report/latest','agent report includes technical role'),
('TradingAgents / fundamental','INTERACTIVE','/api/v1/agents/report/latest','agent report includes fundamental role'),
('TradingAgents / sentiment','INTERACTIVE','/api/v1/agents/debate/latest','agent debate/report'),
('TradingAgents / risk','INTERACTIVE','/api/v1/agents/risk-review/latest','agent risk review'),
('TradingAgents / portfolio manager','INTERACTIVE','/api/v1/agents/portfolio-review/latest','portfolio review'),
('Strategy Engine / ETF rotation','STATIC_PLACEHOLDER',None,'strategy API pending'),
('Strategy Engine / multi-factor stock','INTERACTIVE','/api/v1/strategy/signals/latest','factor strategy dry-run'),
('Strategy Engine / position sizing','INTERACTIVE','/api/v1/strategy/trade-intents/latest','dry-run intents'),
('Risk Gate / trade validator','INTERACTIVE','/api/v1/risk/decisions/latest','risk dry-run'),
('Human Approval','BACKEND_MISSING','/api/v1/approval/status','readonly approval API pending'),
('Paper Trading','BACKEND_MISSING','/api/v1/paper-trading/status','paper API pending'),
('Shadow Trading','BACKEND_MISSING','/api/v1/shadow-trading/report/latest','shadow API pending'),
('Live Trading','DISABLED_FOR_SAFETY','/api/v1/live/status','disabled by default'),
]

def feature_matrix(repo_root='.'):
    return {'stage':STAGE,'features':[{'feature':f,'status':s,'api':a,'note':n,'read_only':True,'no_order_submitted':True} for f,s,a,n in FEATURES],**SAFETY}

def reports_index(repo_root='.'):
    paths=['local_console_xtdata_live_stage87/xtdata_live_report.json','local_console_artifact_migration_stage87/artifact_migration_report.json','local_console_factor_stage79/factor_report.json','local_console_agent_stage81/agent_research_report.json','local_console_backtest_stage82/backtest_dashboard_report.json']
    return {'stage':STAGE,'reports':[{'path':p,'exists':Path(repo_root,p).exists()} for p in paths],**SAFETY}

def dry_run_check(repo_root='.'):
    return {'stage':STAGE,'task_id':'workflow_dry_run_check','status':'SUCCESS','sequence':['GET /api/v1/market/xtdata-live/status','GET /api/v1/datahub/status','POST /api/v1/tasks/run factor_research_dry_run','POST /api/v1/tasks/run agent_research_dry_run','POST /api/v1/tasks/run factor_strategy_dry_run','POST /api/v1/tasks/run risk_gate_dry_run','GET /api/v1/approval/status','GET /api/v1/paper-trading/status'],'message':'dry-run only; no orders submitted',**SAFETY}

def _md(title,obj):
    return '# '+title+'\n\n```json\n'+json.dumps(obj,ensure_ascii=False,indent=2)+'\n```\n'

def write_workflow_outputs(repo_root='.', output_dir='local_console_workflow_stage87'):
    root=Path(repo_root); out=root/output_dir; canon=root/'artifacts/reports/stage87/workflow'; out.mkdir(parents=True,exist_ok=True); canon.mkdir(parents=True,exist_ok=True)
    docs={'workflow_status':workflow_status(repo_root),'workflow_feature_matrix':feature_matrix(repo_root),'workflow_reports_index':reports_index(repo_root),'workflow_dry_run_check':dry_run_check(repo_root)}
    for stem,obj in docs.items():
        for base in (out,canon):
            (base/f'{stem}.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
            (base/f'{stem}.md').write_text(_md(stem,obj),encoding='utf-8')
    return {'output_dir':str(out),'canonical_dir':str(canon),**dry_run_check(repo_root)}
