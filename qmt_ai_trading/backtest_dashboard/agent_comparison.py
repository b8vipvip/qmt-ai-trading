from __future__ import annotations
from .safety import with_safety

def compare_agents(context, shadow, metrics):
    report=context.get('agent_research_report') or {}; agents=report.get('agent_outputs') if isinstance(report,dict) else None
    if not agents: agents=[{'agent_id':'fallback_agent','agent_name':'Fallback Research Agent','recommendation_type':'RESEARCH_ONLY','confidence':0.5,'risk_flags':['fallback_used','mock_data'],'limitations':['missing agent outputs']}]
    out=[]
    for a in agents:
        out.append({'agent_id':a.get('agent_id','agent'),'agent_name':a.get('agent_name','Agent'),'recommendation_type':a.get('recommendation_type','RESEARCH_ONLY'),'confidence':a.get('confidence',0.5),'risk_flags':a.get('risk_flags',[]),'linked_symbols':context.get('linked_symbols',[]),'linked_trade_intents':[x.get('intent_id','mock-intent') for x in context.get('factor_trade_intents',[]) if isinstance(x,dict)],'backtest_summary':{'total_return':metrics.get('total_return'),'max_drawdown':metrics.get('max_drawdown'),'win_rate':metrics.get('win_rate')},'agreement_score':0.55 if metrics.get('total_return',0)>=0 else 0.35,'disagreement_points':['agreement_score is research-only, not a trade signal','mock/fallback data cannot support live decisions'],'risk_consistency':'consistent_with_risk_gate' if metrics.get('risk_rejected_count',0)>=0 else 'unknown','limitations':a.get('limitations',[]) + ['该结果仅用于前端联调和研究展示，不能作为实盘依据。'],'research_only':True,'dry_run':True,'not_live_trading':True})
    return with_safety({'agent_backtest_comparison':out,'comparison_logic':['Agent 看多观点 vs 回测收益','Risk Agent 观点 vs RiskDecision 阻断原因','Portfolio Manager 观点 vs 组合风险收益']})
