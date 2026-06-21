import json
from pathlib import Path
from qmt_ai_trading.backtest_dashboard import run_backtest_dashboard
from qmt_ai_trading.backtest_dashboard.input_loader import build_context

REQUIRED=['backtest_input_context','shadow_replay_result','performance_metrics','performance_attribution','agent_backtest_comparison','backtest_dashboard_report','frontend_backtest_contract','next_monitoring_alert_plan']

def test_context_fallback_safe(tmp_path):
    ctx=build_context(tmp_path)
    assert ctx['fallback_used'] is True and ctx['mock_data'] is True
    assert ctx['dry_run'] and ctx['not_live_trading'] and ctx['research_only']


def test_stage82_outputs_required_files(tmp_path):
    res=run_backtest_dashboard(tmp_path,'out')
    od=tmp_path/'out'
    for n in REQUIRED:
        assert (od/f'{n}.json').exists(), n
        assert (od/f'{n}.md').exists(), n
    metrics=json.loads((od/'performance_metrics.json').read_text(encoding='utf-8'))
    for k in ['total_return','annualized_return','max_drawdown','volatility','sharpe_like','win_rate','trade_count','turnover','avg_holding_days','risk_rejected_count','approved_dry_run_count','fallback_used','mock_data','data_quality']:
        assert k in metrics
    assert res['dry_run'] and res['not_live_trading'] and res['research_only']


def test_agent_backtest_comparison_shape(tmp_path):
    run_backtest_dashboard(tmp_path,'out')
    comp=json.loads((tmp_path/'out/agent_backtest_comparison.json').read_text(encoding='utf-8'))
    row=comp['agent_backtest_comparison'][0]
    for k in ['agent_id','agent_name','recommendation_type','confidence','risk_flags','linked_symbols','linked_trade_intents','backtest_summary','agreement_score','disagreement_points','risk_consistency','limitations','research_only','dry_run','not_live_trading']:
        assert k in row
    assert row['research_only'] and row['dry_run'] and row['not_live_trading']
