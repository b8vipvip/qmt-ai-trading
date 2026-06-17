"""QMT historical market-data field alias mapping.

Only historical quote/bar fields are handled here. Trading fields such as
accounts, positions, orders, or executions are intentionally out of scope.
"""

from __future__ import annotations

from typing import Any, Mapping

QMT_REQUIRED_BAR_FIELDS = ("datetime", "open", "high", "low", "close")
QMT_OPTIONAL_BAR_FIELDS = ("volume", "amount", "symbol", "frequency")
QMT_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "datetime": ("datetime", "time", "date", "index", "stime"),
    "open": ("open", "openPrice", "open_price"),
    "high": ("high", "highPrice", "high_price"),
    "low": ("low", "lowPrice", "low_price"),
    "close": ("close", "closePrice", "close_price"),
    "volume": ("volume", "vol"),
    "amount": ("amount", "turnover"),
    "symbol": ("symbol", "code", "stock_code", "instrument"),
    "frequency": ("frequency", "period"),
}


def _lookup(record: Mapping[str, Any], aliases: tuple[str, ...]) -> Any:
    for alias in aliases:
        if alias in record:
            return record[alias]
    lower_map = {str(key).lower(): key for key in record}
    for alias in aliases:
        key = lower_map.get(alias.lower())
        if key is not None:
            return record[key]
    return None


def resolve_qmt_field(record: Mapping[str, Any], canonical_name: str) -> Any:
    """Resolve a canonical QMT bar field from a raw record using aliases."""

    aliases = QMT_FIELD_ALIASES.get(canonical_name, (canonical_name,))
    return _lookup(record, aliases)


def map_qmt_record_fields(record: Mapping[str, Any]) -> dict[str, Any]:
    """Map known raw QMT bar aliases to canonical bar field names."""

    return {name: value for name in QMT_FIELD_ALIASES if (value := resolve_qmt_field(record, name)) is not None}
