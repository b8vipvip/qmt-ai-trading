"""Standard read-only QMT account query gateway.

No QMT connection or client startup occurs at import time. All account access is
triggered explicitly by the public query functions below.
"""

from __future__ import annotations

from typing import Any

from qmt_ai_trading.config.settings import get_settings


def _readonly_client() -> Any:
    """Create the existing lazy read-only trade client from environment settings."""

    from qmt_gateway.trade_readonly_client import QmtTradeReadonlyClient

    settings = get_settings()
    return QmtTradeReadonlyClient(
        {"account_id": settings.qmt_account_id, "qmt_userdata_path": settings.qmt_userdata_path}
    )


def get_account_asset() -> Any:
    """Return account asset information through the read-only adapter."""

    return _readonly_client().query_asset()


def get_positions() -> Any:
    """Return current positions through the read-only adapter."""

    return _readonly_client().query_positions()


def get_orders() -> Any:
    """Return current orders through the read-only adapter."""

    return _readonly_client().query_orders()


def get_trades() -> Any:
    """Return current trades through the read-only adapter."""

    return _readonly_client().query_trades()


class QmtAccountGateway:
    """Account, cash, position, order, and trade query wrapper."""

    def get_account_snapshot(self) -> dict[str, Any]:
        """Return the existing read-only account snapshot format."""

        return _readonly_client().snapshot()

    def get_account_asset(self) -> Any:
        return get_account_asset()

    def get_positions(self) -> Any:
        return get_positions()

    def get_orders(self) -> Any:
        return get_orders()

    def get_trades(self) -> Any:
        return get_trades()
