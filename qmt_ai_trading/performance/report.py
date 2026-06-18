from __future__ import annotations
from qmt_ai_trading.performance.attribution import attribute_by_risk_gate, attribute_by_symbol, format_factor_attribution

SAFETY_NOTE="Long backtest is dry-run simulation only and is not an order instruction."

def format_long_backtest_markdown(result):
    s=result.summary
    symbol_attr=attribute_by_symbol(result.trades, result.equity_curve)
    risk_attr=attribute_by_risk_gate(result.trades)
    lines=["# Long Portfolio Backtest Report","", "## Backtest period", f"- Start: {result.period.start_date}", f"- End: {result.period.end_date}", f"- Frequency: {result.period.frequency}", f"- Rebalance frequency: {result.period.rebalance_frequency}", "", "## Data source / cache quality", f"- Data source: {result.data_source}", f"- Cache quality: {result.cache_quality}", "", "## Performance summary"]
    if s:
        lines += [f"- Initial cash: {s.initial_cash:.2f}", f"- Final equity: {s.final_equity:.2f}", f"- Total return: {s.total_return:.2%}", f"- Annualized return: {s.annualized_return:.2%}", f"- Max drawdown: {s.max_drawdown:.2%} (non-positive ratio)", f"- Volatility / Sharpe: {s.volatility:.2%} / {s.sharpe:.4f}", f"- Win rate: {s.win_rate:.2%}", f"- Turnover: {s.turnover:.4f}", f"- Rebalance count: {s.rebalance_count}", f"- Trade count: {s.trade_count}", f"- Risk blocked count: {s.risk_blocked_count}"]
    lines += ["", "## Equity curve summary", f"- Points: {len(result.equity_curve)}", "", "## Factor attribution", format_factor_attribution(result.factor_attribution), "", "## Symbol attribution", "```json", str(symbol_attr), "```", "", "## Risk Gate attribution", "```json", str(risk_attr), "```", "", "## Warnings"]
    lines += [f"- {w}" for w in (result.warnings or ["None"])]
    lines += ["", "## Safety note", SAFETY_NOTE]
    return "\n".join(lines)+"\n"
