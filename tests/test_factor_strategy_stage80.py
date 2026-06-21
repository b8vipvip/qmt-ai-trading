from qmt_ai_trading.research.factor_engine import run_factor_scan
from qmt_ai_trading.strategies.factor_strategy_engine import build_factor_strategy
from qmt_ai_trading.risk.factor_strategy_risk_review import review_trade_intents
from qmt_ai_trading.console_api.task_runner import run_task
from qmt_ai_trading.console_api.task_store import TaskStore


def test_factor_candidates_to_trade_intents_and_risk_gate():
    scan = run_factor_scan({'factor_set':['momentum_20d','volatility_20d','volume_ratio_20d']})
    built = build_factor_strategy(scan['factor_candidates'], max_positions=2)
    assert built['strategy_signals']
    intents = built['trade_intents']
    assert intents and all(i['source']=='factor_strategy_stage80' and i['dry_run'] is True for i in intents)
    assert all('mock_data' in i['risk_flags'] and 'not_live_trading' in i['risk_flags'] for i in intents)
    decisions = review_trade_intents(intents)
    assert decisions and all(d['decision']=='REJECTED_DRY_RUN' and d['reasons'] for d in decisions)
    blob = str(built) + str(decisions)
    assert 'xttrader' not in blob.lower()
    assert all(d['no_order_submitted'] and d['no_account_query'] and not d['auto_approve'] for d in decisions)


def test_factor_strategy_task_registry_dry_run():
    run = run_task('factor_strategy_dry_run', {'max_positions':2}, TaskStore())
    assert run.status == 'SUCCESS'
    assert run.output['trade_intents'][0]['dry_run'] is True
    assert run.output['trade_intents'][0]['source'] == 'factor_strategy_stage80'
    assert run.output['risk_decisions'][0]['reasons']
    assert run.output['no_qmt_trader_api'] and run.output['no_account_query'] and run.output['no_order_submitted']
    assert run.output['auto_approve'] is False
