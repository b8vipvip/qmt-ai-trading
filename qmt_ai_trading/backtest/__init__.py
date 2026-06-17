"""Stage 8 lightweight backtest and shadow replay interfaces."""

from qmt_ai_trading.backtest.metrics import (
    compute_equity_curve,
    compute_max_drawdown,
    compute_total_return,
    compute_win_rate,
    summarize_backtest_result,
)
from qmt_ai_trading.backtest.models import BacktestAccount, BacktestOrder, BacktestPosition, BacktestResult, BacktestTrade
from qmt_ai_trading.backtest.simulator import run_simple_backtest, simulate_order_fill, simulate_trade_intents, update_backtest_account

__all__ = [
    "BacktestAccount", "BacktestOrder", "BacktestPosition", "BacktestResult", "BacktestTrade",
    "compute_equity_curve", "compute_max_drawdown", "compute_total_return", "compute_win_rate", "summarize_backtest_result",
    "run_simple_backtest", "simulate_order_fill", "simulate_trade_intents", "update_backtest_account",
]
