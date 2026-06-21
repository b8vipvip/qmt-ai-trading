from __future__ import annotations
from .xtdata_config import XtDataAdapterConfig

DISABLED_MESSAGE = "xtdata adapter is disabled by safety gate"

class XtDataAdapterBoundary:
    """Dry-run boundary for a future real xtdata adapter.

    future import target: "xtquant.xtdata". Stage85 deliberately never imports it.
    """
    def __init__(self, config: XtDataAdapterConfig | None = None):
        self.config = config or XtDataAdapterConfig()

    def _base(self, status: str = "DISABLED", message: str = DISABLED_MESSAGE) -> dict:
        c = self.config
        return {
            "status": status,
            "enabled": c.enabled,
            "dry_run": c.dry_run,
            "read_only": c.read_only,
            "real_market_data": False,
            "xtdata_imported": False,
            "mini_qmt_connected": False,
            "sandbox_fallback": c.sandbox_fallback,
            "allow_xttrader": c.allow_xttrader,
            "no_order_submitted": True,
            "no_qmt_trader_api": True,
            "message": message,
        }

    def check_config(self) -> dict:
        result = self._base()
        result.update({"config": self.config.to_dict(), "warnings": [DISABLED_MESSAGE]})
        return result

    def probe_import(self) -> dict:
        result = self._base()
        result.update({"import_attempted": False, "import_allowed": self.config.allow_import_xtdata})
        return result

    def probe_connection(self) -> dict:
        result = self._base()
        result.update({"connection_attempted": False, "connect_allowed": self.config.allow_connect_miniqmt})
        return result

    def get_snapshot(self, symbols: list[str]) -> dict:
        result = self._base()
        result.update({"symbols": list(symbols), "snapshots": []})
        return result

    def get_bars(self, symbol: str, timeframe: str, limit: int = 100) -> dict:
        result = self._base()
        result.update({"symbol": symbol, "timeframe": timeframe, "limit": limit, "bars": []})
        return result

    def subscribe(self, symbols: list[str]) -> dict:
        result = self._base()
        result.update({"symbols": list(symbols), "subscribed": False})
        return result
