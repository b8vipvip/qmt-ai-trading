from __future__ import annotations
from typing import Any
from .xtdata_live_config import XtDataLiveReadOnlyConfig
from .sandbox_gateway import SandboxMarketDataGateway
from qmt_ai_trading.common.json_safe import json_safe

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
            if hasattr(xtdata, "get_market_data_ex"):
                raw = xtdata.get_market_data_ex([], [symbol], period=period, count=limit)
            else:
                raw = xtdata.get_market_data([], [symbol], period=period, count=limit)
            return {**self._base("REAL_MARKET_DATA", True), "symbol": symbol, "period": period, "limit": limit, "bars": _normalize_bars(raw, symbol)}
        except Exception as exc:
            bars = [b.to_dict() for b in self._sandbox.get_bars(symbol, period, min(limit, 100))]
            return {**self._base("FALLBACK_TO_SANDBOX", False), "symbol": symbol, "period": period, "limit": limit, "bars": bars, "get_market_data_ex_error": f"{type(exc).__name__}: {exc}", "error_message": f"{type(exc).__name__}: {exc}"}

def _normalize_snapshots(raw: Any) -> list[dict]:
    safe = json_safe(raw)
    if isinstance(safe, dict):
        return [{"symbol": k, **(v if isinstance(v, dict) else {"value": v})} for k, v in safe.items()]
    if isinstance(safe, list):
        return [v if isinstance(v, dict) else {"value": v} for v in safe]
    return [{"value": safe}]

def _normalize_bars(raw: Any, symbol: str) -> list[dict]:
    safe = json_safe(raw)
    rows: list[dict] = []
    if isinstance(safe, dict):
        if symbol in safe:
            candidate = safe[symbol]
            if isinstance(candidate, list):
                rows = [r if isinstance(r, dict) else {"value": r} for r in candidate]
            elif isinstance(candidate, dict):
                rows = _column_dict_to_rows(candidate)
        if not rows:
            rows = _column_dict_to_rows(safe)
    elif isinstance(safe, list):
        rows = [r if isinstance(r, dict) else {"value": r} for r in safe]
    else:
        rows = [{"value": safe}]

    normalized = []
    for row in rows:
        item = dict(row)
        item.setdefault("symbol", symbol)
        for source, target in (("index", "time"), ("stime", "time"), ("datetime", "time"), ("timestamp", "time")):
            if source in item and target not in item:
                item[target] = item[source]
        item.update({"read_only": True, "no_xttrader": True, "no_order_submitted": True, "no_account_query": True})
        normalized.append(json_safe(item))
    return normalized

def _column_dict_to_rows(data: dict) -> list[dict]:
    if not data:
        return []
    values = list(data.values())
    if values and all(isinstance(v, list) for v in values):
        max_len = max((len(v) for v in values), default=0)
        return [{k: (v[i] if i < len(v) else None) for k, v in data.items()} for i in range(max_len)]
    return [data]
