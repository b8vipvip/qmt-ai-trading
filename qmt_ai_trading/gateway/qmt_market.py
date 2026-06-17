"""Standard read-only QMT market data gateway.

Importing this module does not connect to QMT. Adapter calls are made only when
an explicit function is invoked and can be expanded as existing xtdata scripts
are migrated behind this interface.
"""

from __future__ import annotations

from typing import Any


def _data_client() -> Any:
    """Return the existing lazy QMT data client adapter."""

    from qmt_gateway.data_client import QmtDataClient

    return QmtDataClient()


def get_latest_price(symbol: str) -> Any:
    """Return the latest price for ``symbol`` via a safe read-only adapter.

    TODO(stage2): map the existing local QMT quote conventions into a stable
    return model. For now this calls the lazy data client only when invoked.
    """

    client = _data_client()
    data = client.safe_call(
        "get_market_data",
        field_list=["close"],
        stock_list=[symbol],
        period="1d",
        count=1,
    )
    return data


def get_bars(symbol: str, period: str = "1d", count: int = 100) -> Any:
    """Return recent bars for ``symbol`` via the existing read-only adapter."""

    client = _data_client()
    return client.safe_call(
        "get_market_data",
        field_list=["open", "high", "low", "close", "volume", "amount"],
        stock_list=[symbol],
        period=period,
        count=count,
    )


class QmtMarketGateway:
    """Read-only market data interface wrapper."""

    def get_latest_quote(self, symbol: str) -> dict[str, Any]:
        """Return the latest quote payload for a symbol."""

        return {"symbol": symbol, "raw": get_latest_price(symbol)}

    def get_latest_price(self, symbol: str) -> Any:
        """Return the latest price payload for a symbol."""

        return get_latest_price(symbol)

    def get_bars(self, symbol: str, period: str = "1d", count: int = 100) -> Any:
        """Return recent bar payload for a symbol."""

        return get_bars(symbol, period=period, count=count)
