"""Research factor placeholders.

Stage one does not introduce a qlib dependency. Future research work may refer
to Qlib and vnpy.alpha ideas such as Alpha158, Alpha101, LightGBM, IC, and
RankIC, but those projects are not copied into this repository.
"""

from __future__ import annotations

from typing import Iterable


def list_placeholder_factors() -> list[str]:
    """Return placeholder factor names for structure validation only."""

    return ["momentum_placeholder", "volatility_placeholder"]


def calculate_factor_snapshot(symbols: Iterable[str]) -> dict[str, dict[str, float | None]]:
    """Return an empty factor snapshot shape without importing research engines.

    TODO: Add validated factor implementations after data contracts and offline
    backtest evaluation are ready.
    """

    return {symbol: {"score": None} for symbol in symbols}
