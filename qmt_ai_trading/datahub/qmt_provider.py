"""Optional QMT/xtquant historical data provider.

This module intentionally does not import ``xtquant`` at module import time.
Only explicit QMT provider use attempts to load ``xtquant.xtdata``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Mapping

from qmt_ai_trading.datahub.local_store import BarQuery
from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.symbols import normalize_symbol


class QmtProviderError(Exception):
    """Raised when the optional QMT historical provider cannot be used."""


def _import_xtdata() -> Any:
    """Import xtquant.xtdata lazily so mock/offline workflows keep working."""

    try:
        from xtquant import xtdata  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local QMT install
        raise QmtProviderError("xtquant.xtdata is not available; install/enable MiniQMT/QMT Python environment first") from exc
    return xtdata


def _iso_day(value: date | datetime | str) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    return text


def _qmt_day(value: date | datetime | str) -> str:
    return _iso_day(value).replace("-", "")


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _frequency_to_period(frequency: str) -> str:
    mapping = {"1d": "1d", "day": "1d", "1m": "1m", "5m": "5m"}
    normalized = str(frequency).lower().strip()
    if normalized not in mapping:
        raise QmtProviderError(f"unsupported QMT historical frequency: {frequency}; supported: 1d, 1m, 5m")
    return mapping[normalized]


def _records_from_frame(frame: Any) -> list[Mapping[str, Any]]:
    if frame is None:
        return []
    if hasattr(frame, "to_dict"):
        try:
            records = frame.to_dict("records")
            if isinstance(records, list):
                return [row for row in records if isinstance(row, Mapping)]
        except TypeError:
            pass
    if isinstance(frame, list):
        return [row for row in frame if isinstance(row, Mapping)]
    if isinstance(frame, Mapping):
        # Common simple shape: {field: [values...]}
        if any(isinstance(value, (list, tuple)) for value in frame.values()):
            length = max((len(value) for value in frame.values() if isinstance(value, (list, tuple))), default=0)
            rows: list[Mapping[str, Any]] = []
            for index in range(length):
                rows.append({key: (value[index] if isinstance(value, (list, tuple)) and index < len(value) else value) for key, value in frame.items()})
            return rows
        return [frame]
    return []


def _extract_symbol_payload(raw: Any, symbol: str) -> Any:
    normalized = normalize_symbol(symbol)
    if raw is None:
        return None
    if isinstance(raw, Mapping):
        return raw.get(symbol) or raw.get(normalized) or raw.get("bars") or raw
    return raw


def _bar_from_row(symbol: str, row: Mapping[str, Any]) -> MarketBar:
    normalized = normalize_symbol(symbol)
    return MarketBar(
        symbol=normalize_symbol(str(row.get("symbol") or normalized)),
        datetime=row.get("datetime") or row.get("date") or row.get("time") or row.get("stime"),
        open=_to_float(row.get("open")),
        high=_to_float(row.get("high")),
        low=_to_float(row.get("low")),
        close=_to_float(row.get("close")),
        volume=_to_float(row.get("volume") or row.get("vol")),
        amount=_to_float(row.get("amount") or row.get("turnover")),
        source="qmt",
    )


@dataclass
class QmtHistoricalDataProvider:
    """Read historical bars from local QMT/xtquant ``xtdata`` APIs only."""

    auto_connect: bool = False
    xtdata_module: Any = None
    metadata: dict[str, Any] | None = None
    name: str = field(default="qmt", init=False)

    def __post_init__(self) -> None:
        self.metadata = dict(self.metadata or {})
        self._xtdata = self.xtdata_module
        if self.auto_connect:
            self.connect()

    def _ensure_xtdata(self) -> Any:
        if self._xtdata is None:
            self._xtdata = _import_xtdata()
        return self._xtdata

    def is_available(self) -> bool:
        try:
            self._ensure_xtdata()
            return True
        except QmtProviderError:
            return False

    def connect(self) -> bool:
        xtdata = self._ensure_xtdata()
        connect = getattr(xtdata, "connect", None)
        if callable(connect):
            try:
                result = connect()
            except Exception as exc:  # pragma: no cover - local QMT dependent
                raise QmtProviderError(f"xtdata.connect() failed: {exc}") from exc
            return True if result is None else bool(result)
        return True

    def fetch_bars(self, query: BarQuery) -> list[MarketBar]:
        self._validate_query(query)
        xtdata = self._ensure_xtdata()
        period = _frequency_to_period(query.frequency)
        start_time = _qmt_day(query.start_date)
        end_time = _qmt_day(query.end_date)
        bars: list[MarketBar] = []
        for symbol in query.symbols:
            normalized = normalize_symbol(symbol)
            download = getattr(xtdata, "download_history_data", None)
            if not callable(download):
                raise QmtProviderError("xtdata.download_history_data is not available")
            download(normalized, period, start_time=start_time, end_time=end_time)
            raw = self._get_market_data(xtdata, normalized, period, start_time, end_time)
            payload = _extract_symbol_payload(raw, normalized)
            bars.extend(_bar_from_row(normalized, row) for row in _records_from_frame(payload))
        return bars

    def get_bars(self, query: BarQuery) -> list[MarketBar]:
        """Compatibility wrapper for the Data Hub provider protocol."""

        return self.fetch_bars(query)

    def _get_market_data(self, xtdata: Any, symbol: str, period: str, start_time: str, end_time: str) -> Any:
        get_ex = getattr(xtdata, "get_market_data_ex", None)
        if callable(get_ex):
            return get_ex([], [symbol], period=period, start_time=start_time, end_time=end_time)
        get_data = getattr(xtdata, "get_market_data", None)
        if callable(get_data):
            return get_data([], [symbol], period=period, start_time=start_time, end_time=end_time)
        raise QmtProviderError("xtdata.get_market_data_ex/get_market_data is not available")

    def _validate_query(self, query: BarQuery) -> None:
        if not query.symbols:
            raise QmtProviderError("query.symbols must not be empty")
        if not _iso_day(query.start_date) or not _iso_day(query.end_date):
            raise QmtProviderError("query.start_date and query.end_date are required")
        _frequency_to_period(query.frequency)
