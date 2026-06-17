"""ETF rotation strategy shell."""

from __future__ import annotations

from qmt_ai_trading.common.types import TradeIntent


def generate_etf_rotation_signal(symbol: str = "510300.SH") -> TradeIntent:
    """Return a dry-run ETF rotation example signal without placing orders."""

    return TradeIntent(
        symbol=symbol,
        side="HOLD",
        quantity=0,
        target_percent=0.0,
        price_type="LATEST",
        reason="stage-1 ETF rotation placeholder; no live order submission",
        source="strategy_engine.etf_rotation",
        dry_run=True,
    )
