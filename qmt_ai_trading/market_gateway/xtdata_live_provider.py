from __future__ import annotations
from typing import Any
from .xtdata_live_config import XtDataLiveReadOnlyConfig
from .sandbox_gateway import SandboxMarketDataGateway

BASE_FLAGS = {
    "provider": "xtdata_live_readonly",
    "read_only": True,
    "no_xttrader": True,
    "no_order_submitted": True,
    "no_account_query": True,
    "not_live_trading": True,
}

def _import_xtdata(config: XtDataLiveReadOnlyConfig):
    if not config.allow_import_xtdata:
        return None, "DISABLED"
    try:
        from xtquant import xtdata  # type: ignore
        return xtdata, "IMPORTED"
    except Exception as exc:
        return None, f"IMPORT_FAILED:{type(exc).__name__}"

class XtDataLiveReadOnlyProvider:
    def __init__(self, config: XtDataLiveReadOnlyConfig | None = None):
        self.config = config or XtDataLiveReadOnlyConfig()
        self._sandbox = SandboxMarketDataGateway(provider_type="mock_provider")
        self._xtdata = None
        self._import_status = "NOT_ATTEMPTED"

    def _enabled_for_real(self) -> bool:
        c = self.config
        return bool(c.enabled and c.allow_import_xtdata and c.allow_real_market_data and c.allow_connect_miniqmt and c.read_only and not c.allow_xttrader and not c.allow_account_query and not c.allow_order_submit)

    def _base(self, status: str, real: bool = False) -> dict:
        return {**BASE_FLAGS, "status": status, "real_market_data": real, "sandbox_fallback": (not real) and self.config.sandbox_fallback, "allow_xttrader": False, "allow_order_submit": False, "allow_account_query": False, "import_status": self._import_status, "xtdata_imported": self._import_status == "IMPORTED"}

    def _ensure_xtdata(self):
        if not self._enabled_for_real():
            self._import_status = "DISABLED"
            return None
        if self._xtdata is None:
            self._xtdata, self._import_status = _import_xtdata(self.config)
        return self._xtdata

    def get_status(self) -> dict:
        xtdata = self._ensure_xtdata()
        if xtdata is None:
            return {**self._base("FALLBACK_TO_SANDBOX", False), "mini_qmt_connected": False, "symbols": self.config.symbols, "error_message": "xtdata real readonly mode is disabled or unavailable; using sandbox fallback"}
        return {**self._base("XTData_AVAILABLE_READONLY", True), "mini_qmt_connected": True, "symbols": self.config.symbols}

    def get_snapshot(self, symbols: list[str]) -> dict:
        xtdata = self._ensure_xtdata()
        if xtdata is None:
            snaps = [s.to_dict() for s in self._sandbox.get_snapshot(symbols)]
            return {**self._base("FALLBACK_TO_SANDBOX", False), "symbols": symbols, "snapshots": snaps}
        try:
            raw = xtdata.get_full_tick(symbols) or {}
            return {**self._base("SUCCESS", True), "symbols": symbols, "snapshots": _normalize_snapshots(raw)}
        except Exception as exc:
            snaps = [s.to_dict() for s in self._sandbox.get_snapshot(symbols)]
            return {**self._base("FALLBACK_TO_SANDBOX", False), "symbols": symbols, "snapshots": snaps, "get_full_tick_error": f"{type(exc).__name__}: {exc}", "error_message": f"{type(exc).__name__}: {exc}"}

    def get_bars(self, symbol: str, period: str = "1d", limit: int = 100) -> dict:
        xtdata = self._ensure_xtdata()
        if xtdata is None:
            bars = [b.to_dict() for b in self._sandbox.get_bars(symbol, period, min(limit, 100))]
            return {**self._base("FALLBACK_TO_SANDBOX", False), "symbol": symbol, "period": period, "limit": limit, "bars": bars}
        try:
            raw = xtdata.get_market_data([], [symbol], period=period, count=limit)
            return {**self._base("SUCCESS", True), "symbol": symbol, "period": period, "limit": limit, "bars": _normalize_bars(raw, symbol)}
        except Exception as exc:
            bars = [b.to_dict() for b in self._sandbox.get_bars(symbol, period, min(limit, 100))]
            return {**self._base("FALLBACK_TO_SANDBOX", False), "symbol": symbol, "period": period, "limit": limit, "bars": bars, "get_market_data_ex_error": f"{type(exc).__name__}: {exc}", "error_message": f"{type(exc).__name__}: {exc}"}

def _normalize_snapshots(raw: Any) -> list[dict]:
    if isinstance(raw, dict):
        return [{"symbol": k, **(v if isinstance(v, dict) else {"value": str(v)})} for k, v in raw.items()]
    return [{"value": str(raw)}]

def _normalize_bars(raw: Any, symbol: str) -> list[dict]:
    if hasattr(raw, "to_dict"):
        raw = raw.to_dict()
    return [{"symbol": symbol, "raw": raw if isinstance(raw, (dict, list)) else str(raw)}]
