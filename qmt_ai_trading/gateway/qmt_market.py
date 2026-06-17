"""QMT market data gateway shell.

This module intentionally does not modify or replace existing working QMT code.
Future implementations should adapt existing xtdata calls behind this interface.
"""

from __future__ import annotations

from typing import Any


class QmtMarketGateway:
    """Read-only market data interface placeholder."""

    def get_latest_quote(self, symbol: str) -> dict[str, Any]:
        """Return the latest quote for a symbol.

        TODO: Wire this to the existing QMT xtdata market data implementation.
        """

        raise NotImplementedError("QMT market data adapter is not implemented yet")
