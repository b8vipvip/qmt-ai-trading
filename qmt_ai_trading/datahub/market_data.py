"""Market data hub placeholders."""

from __future__ import annotations

from typing import Any


def get_market_snapshot(symbol: str) -> dict[str, Any]:
    """Return a market data placeholder.

    TODO: Route market data through a unified Data Hub while preserving existing
    working QMT market data scripts.
    """

    return {"symbol": symbol, "data": None, "status": "not_implemented"}
