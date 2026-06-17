from unittest import mock

from qmt_ai_trading.backtest.metrics import compute_max_drawdown, compute_total_return, compute_win_rate, summarize_backtest_result
from qmt_ai_trading.backtest.models import BacktestAccount, BacktestOrder, BacktestPosition, BacktestResult, BacktestTrade
from qmt_ai_trading.backtest.shadow_replay import ShadowReplayResult, replay_trade_intents
from qmt_ai_trading.backtest.simulator import run_simple_backtest, simulate_order_fill, update_backtest_account
from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.strategies.etf_rotation import ETFCandidate, generate_etf_rotation_intents, run_etf_rotation_backtest


def test_backtest_models_can_instantiate():
    assert BacktestOrder("510300.SH", "BUY", 100, 4.0)
    assert BacktestTrade("510300.SH", "BUY", 100, 4.0)
    assert BacktestPosition("510300.SH")
    assert BacktestAccount(1000.0)
    assert BacktestResult(1000, 1000, 1000, 0, 0, 0, 0)


def test_simulate_order_fill_generates_trade():
    trade = simulate_order_fill(BacktestOrder("510300.SH", "BUY", 100, 4.0))
    assert trade.amount == 400.0
    assert trade.fee > 0


def test_buy_reduces_cash():
    account = BacktestAccount(cash=1000.0)
    trade = simulate_order_fill(BacktestOrder("510300.SH", "BUY", 100, 4.0))
    update_backtest_account(account, trade, {"510300.SH": 4.0})
    assert account.cash < 1000.0


def test_sell_increases_cash():
    account = BacktestAccount(cash=1000.0, positions={"510300.SH": BacktestPosition("510300.SH", quantity=100, avg_price=4.0)})
    trade = simulate_order_fill(BacktestOrder("510300.SH", "SELL", 100, 4.2))
    update_backtest_account(account, trade, {"510300.SH": 4.2})
    assert account.cash > 1000.0


def test_metrics_compute_normally():
    assert compute_total_return(100, 110) == 0.1
    assert round(compute_max_drawdown([{"equity": 100}, {"equity": 80}, {"equity": 120}]), 2) == 0.2
    assert compute_win_rate([BacktestTrade("a", "SELL", 1, 1, pnl=1), BacktestTrade("a", "SELL", 1, 1, pnl=-1)]) == 0.5


def test_run_simple_backtest_empty_input_not_crash():
    result = run_simple_backtest([], prices={})
    assert result.trade_count == 0
    assert result.final_asset == result.initial_cash


def test_run_simple_backtest_with_trade_intent_returns_result():
    intent = TradeIntent(symbol="510300.SH", side="BUY", quantity=100, source="test")
    result = run_simple_backtest([intent], prices={"510300.SH": 4.0}, initial_cash=10000)
    assert isinstance(result, BacktestResult)
    assert result.trade_count == 1


def test_replay_trade_intents_returns_shadow_result():
    result = replay_trade_intents([TradeIntent(symbol="510300.SH", side="BUY", quantity=100)], {"510300.SH": 4.0})
    assert isinstance(result, ShadowReplayResult)
    assert result.report["event_count"] == 1


def test_etf_strategy_dry_run_intent_can_enter_backtest():
    intents = generate_etf_rotation_intents([ETFCandidate("510300.SH", score=90, last_price=4.0)], capital=10000)
    result = run_simple_backtest(intents, prices={"510300.SH": 4.0}, initial_cash=10000)
    assert result.trade_count == 1
    adapter_result = run_etf_rotation_backtest([ETFCandidate("510300.SH", score=90, last_price=4.0)], {"510300.SH": 4.0}, initial_cash=10000)
    assert adapter_result.trade_count == 1


def test_backtest_does_not_call_real_qmt_order_place_order():
    with mock.patch("qmt_ai_trading.gateway.qmt_order.place_order") as place_order:
        run_simple_backtest([TradeIntent(symbol="510300.SH", side="BUY", quantity=100)], {"510300.SH": 4.0})
    place_order.assert_not_called()


def test_backtest_does_not_modify_risk_gate_logic():
    from qmt_ai_trading.risk.trade_validator import validate_trade_intent

    decision = validate_trade_intent(TradeIntent(symbol="510300.SH", side="BUY", quantity=100))
    assert decision.allowed


def test_backtest_result_summary():
    result = run_simple_backtest([TradeIntent(symbol="510300.SH", side="BUY", quantity=100)], {"510300.SH": 4.0})
    summary = summarize_backtest_result(result)
    assert summary["trade_count"] == 1
    assert "total_return" in summary
