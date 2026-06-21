from __future__ import annotations
from pathlib import Path
from .agent_roles import AGENT_ROLES
from .context_builder import build_context
from .model_usage_loader import load_model_usage
from .models import AgentOutput, now_iso
from .safety import validate_agent_output, validate_report
from .debate import build_debate
from .risk_review import build_risk_review
from .report import write_json, write_md

def _agent(role, name, desc, model_id, context):
    warnings=context.get('warnings', [])
    flags=['dry_run','not_live_trading','research_only'] + (['fallback_used','mock_data'] if context.get('fallback_used') else [])
    if role=='risk_agent': rec='RISK_WARNING'; summary='复核上游 Risk Gate dry-run 结果，所有实盘相关动作保持阻断。'
    elif role=='portfolio_manager_agent': rec='PORTFOLIO_REVIEW'; summary='组合层仅建议人工复核观察清单，不生成订单。'
    elif role=='final_summary_agent': rec='RESEARCH_ONLY'; summary='汇总多 Agent 观点，声明本报告不能作为实盘依据。'
    else: rec='RESEARCH_ONLY'; summary=f'{name} 基于 Stage78/79/80 本地文件进行研究解释。'
    return validate_agent_output(AgentOutput(role,name,desc,model_id,[s['path'] for s in context['input_sources']],summary,[
        '读取模型用途映射、因子候选、策略信号、TradeIntent 与 RiskDecision。',
        '仅进行分析、解释、对比、风险提示、多空辩论和组合复核。',
        '上游 dry-run / mock / fallback 标记必须保留，不能升级为实盘依据。'
    ],0.55 if warnings else 0.72,flags,warnings or ['本地 mock agent 模式，不调用真实 AI。'],rec).to_dict())

def build_frontend_contract():
    return {'page':'Agent 投研','apis':['GET /api/v1/agents/context','GET /api/v1/agents/model-usage','GET /api/v1/agents/runs/latest','GET /api/v1/agents/debate/latest','GET /api/v1/agents/risk-review/latest','GET /api/v1/agents/portfolio-review/latest','GET /api/v1/agents/report/latest','POST /api/v1/tasks/run task_id=agent_research_dry_run'], 'buttons':['运行 Agent 投研 dry-run','刷新 Agent 报告','查看输入上下文','查看多空辩论','查看风险审查','查看组合建议'], 'safety':{'dry_run':True,'not_live_trading':True,'research_only':True,'no_order_submitted':True,'no_qmt_trader_api':True,'requires_risk_gate':True,'requires_human_approval':True}}

def run_agent_research(repo_root='.', output_dir='local_console_agent_stage81', mock_agent=True, real_ai_call=False, max_agents=7, input_source='stage80', dry_run=True):
    root=Path(repo_root); out=root/output_dir; out.mkdir(parents=True, exist_ok=True)
    context=build_context(root); context.update({'mock_agent':mock_agent,'real_ai_call':real_ai_call,'input_source':input_source,'dry_run':True,'not_live_trading':True})
    usage=load_model_usage(root); write_json(out/'agent_context.json', context); write_md(out/'agent_context.md','Stage81 Agent Research Context', {'warnings':context['warnings'],'summary':'Agent Research Context Builder 已读取 Stage78/79/80 本地输出。'})
    write_json(out/'agent_model_usage.json', usage)
    roles=AGENT_ROLES[:max_agents]
    outputs=[_agent(r,n,d,usage['mappings'].get(r,'mock-local-agent'),context) for r,n,d in roles]
    write_json(out/'agent_runs.json', outputs)
    debate=build_debate(outputs); write_json(out/'agent_debate.json', debate); write_md(out/'agent_debate.md','Stage81 Agent Debate', debate)
    risk=build_risk_review(outputs, context); write_json(out/'agent_risk_review.json', risk); write_md(out/'agent_risk_review.md','Stage81 Agent Risk Review', {'warnings':risk['risk_flags'],'summary':risk['summary']})
    portfolio=next((o for o in outputs if o['agent_id']=='portfolio_manager_agent'),{})
    portfolio_review={'dry_run':True,'not_live_trading':True,'research_only':True,'review':portfolio,'summary':'组合经理建议仅为 PORTFOLIO_REVIEW，不提交订单。'}; write_json(out/'agent_portfolio_review.json', portfolio_review)
    report=validate_report({'stage':'Stage81','created_at':now_iso(),'summary':'TradingAgents 多 Agent 投研 dry-run 已完成；报告仅供研究，不作为实盘依据。','agent_outputs':outputs,'debate':debate,'risk_review':risk,'portfolio_review':portfolio_review,'warnings':context['warnings'] + ([] if mock_agent else ['real_ai_call_requested_requires_frontend_confirmation_and_masked_key']),'fallback_used':context['fallback_used'],'mock_data':context['mock_data'],'dry_run':True,'not_live_trading':True,'research_only':True,'no_order_submitted':True,'no_qmt_trader_api':True,'requires_risk_gate':True,'requires_human_approval':True})
    write_json(out/'agent_research_report.json', report); write_md(out/'agent_research_report.md','Stage81 Agent Research Report', report)
    contract=build_frontend_contract(); write_json(out/'frontend_agent_contract.json', contract); write_md(out/'frontend_agent_contract.md','Stage81 Frontend Agent Contract', {'summary':'Agent 投研页面展示角色、输入源、报告、安全警示与 dry-run 按钮。'})
    plan={'stage':'Stage82','title':'回测分析与 Agent 研究报告联动看板','dry_run':True,'research_only':True,'items':['Backtest / Shadow Replay 可视化','关联 Agent 研究报告与策略回测结果','对比 Agent 建议、因子评分、策略信号、Risk Gate 决策和回测表现']}
    write_json(out/'next_backtest_dashboard_plan.json', plan); write_md(out/'next_backtest_dashboard_plan.md','Stage82 Plan', {'summary':'Stage82 继续 dry-run / research only，不接实盘。'})
    return {'task_id':'agent_research_dry_run','status':'SUCCESS','output_dir':str(out),'report_path':str(out/'agent_research_report.json'),'dry_run':True,'not_live_trading':True,'warnings':report.get('warnings',[]), **report}
