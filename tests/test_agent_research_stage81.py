from pathlib import Path
import json
from qmt_ai_trading.agents_research.context_builder import build_context
from qmt_ai_trading.agents_research.agent_runner import run_agent_research

def test_agent_context_fallback_safe(tmp_path):
    ctx=build_context(tmp_path)
    assert ctx['fallback_used'] is True and ctx['mock_data'] is True
    assert ctx['dry_run'] and ctx['not_live_trading'] and ctx['research_only']

def test_agent_research_outputs_required_files(tmp_path):
    out='local_console_agent_stage81'
    res=run_agent_research(tmp_path,out)
    od=tmp_path/out
    for n in ['agent_context.json','agent_context.md','agent_model_usage.json','agent_runs.json','agent_debate.json','agent_debate.md','agent_risk_review.json','agent_risk_review.md','agent_portfolio_review.json','agent_research_report.json','agent_research_report.md','frontend_agent_contract.json','frontend_agent_contract.md','next_backtest_dashboard_plan.json','next_backtest_dashboard_plan.md']:
        assert (od/n).exists(), n
    runs=json.loads((od/'agent_runs.json').read_text(encoding='utf-8'))
    assert len(runs)==7
    for r in runs:
        for k in ['agent_id','agent_name','role','model_id','input_sources','summary','arguments','confidence','risk_flags','limitations','recommendation_type','created_at','dry_run','not_live_trading']:
            assert k in r
        assert r['recommendation_type'] in {'RESEARCH_ONLY','WATCHLIST_SUGGESTION','RISK_WARNING','PORTFOLIO_REVIEW','NO_ACTION'}
        assert r['dry_run'] and r['not_live_trading'] and r['research_only']
    assert res['mock_data'] is True and res['no_order_submitted'] is True

def test_agent_defaults_are_mock_no_real_ai(tmp_path):
    run_agent_research(tmp_path,'out')
    ctx=json.loads((tmp_path/'out/agent_context.json').read_text(encoding='utf-8'))
    assert ctx['mock_agent'] is True
    assert ctx['real_ai_call'] is False
