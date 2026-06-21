from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from .input_loader import build_context
from .shadow_adapter import run_shadow_replay
from .performance_metrics import calculate_metrics
from .attribution import build_attribution
from .agent_comparison import compare_agents
from .safety import with_safety, DISCLAIMER

def _write_json(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def _md(title,o): return '# '+title+'\n\n'+'dry_run=true\nnot_live_trading=true\nresearch_only=true\nfallback_used='+str(o.get('fallback_used')).lower()+'\nmock_data='+str(o.get('mock_data')).lower()+'\n\n'+DISCLAIMER+'\n\n```json\n'+json.dumps(o,ensure_ascii=False,indent=2)+'\n```\n'
def _write_pair(out,name,title,obj): _write_json(out/(name+'.json'),obj); (out/(name+'.md')).write_text(_md(title,obj),encoding='utf-8')

def run_backtest_dashboard(repo_root='.', output_dir='local_console_backtest_stage82', backtest_mode='mock_shadow'):
    out=Path(repo_root)/output_dir; out.mkdir(parents=True,exist_ok=True)
    ctx=build_context(repo_root); ctx['backtest_mode']=backtest_mode
    shadow=run_shadow_replay(ctx); metrics=calculate_metrics(shadow,ctx); attr=build_attribution(shadow,metrics,ctx); comp=compare_agents(ctx,shadow,metrics)
    report=with_safety({'stage':'Stage82','created_at':datetime.now(timezone.utc).isoformat(),'summary':'回测分析与 Agent 研究报告联动看板 dry-run 已完成；不生成订单。','output_dir':output_dir,'report_path':str(out/'backtest_dashboard_report.md'),'context':ctx,'shadow_replay_result':shadow,'performance_metrics':metrics,'performance_attribution':attr,'agent_backtest_comparison':comp,'warnings':ctx.get('warnings',[])})
    frontend=with_safety({'page':'回测分析','apis':['GET /api/v1/backtest/context','GET /api/v1/backtest/shadow-replay/latest','GET /api/v1/backtest/performance/latest','GET /api/v1/backtest/attribution/latest','GET /api/v1/backtest/agent-comparison/latest','GET /api/v1/backtest/report/latest','POST /api/v1/tasks/run task_id=backtest_dashboard_dry_run'],'sections':['回测总览卡片','数据源状态卡片','收益 / 回撤 / 波动 / 胜率指标区','Shadow Replay 结果表','TradeIntent 回测映射表','RiskDecision 回测映射表','Agent 观点 vs 回测表现对比区','组合归因区','风险提示区','报告中心跳转']})
    plan=with_safety({'stage':'Stage83 plan','title':'异常监控、告警与熔断 dry-run 看板','goals':['监控数据缺失、任务失败、回测异常、Agent unsafe 输出、Risk Gate 异常','生成 dry-run alert','前端展示告警中心','不真实发送通知','不接实盘','不调用 xttrader']})
    for name,title,obj in [('backtest_input_context','Backtest Input Context',ctx),('shadow_replay_result','Shadow Replay Result',shadow),('performance_metrics','Performance Metrics',metrics),('performance_attribution','Performance Attribution',attr),('agent_backtest_comparison','Agent Backtest Comparison',comp),('backtest_dashboard_report','Backtest Dashboard Report',report),('frontend_backtest_contract','Frontend Backtest Contract',frontend),('next_monitoring_alert_plan','Next Monitoring Alert Plan',plan)]: _write_pair(out,name,title,obj)
    return report
