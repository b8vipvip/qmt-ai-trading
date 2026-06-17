"""Symbol normalization helpers for Data Hub.

The canonical project format is ``000001.SH`` / ``000001.SZ``.  Helpers are
pure string utilities and never connect to network or market data providers.
"""

from __future__ import annotations

import re

_SH_PREFIXES = ("5", "6", "9")
_SZ_PREFIXES = ("0", "1", "2", "3")
_ETF_PREFIXES = ("510", "511", "512", "513", "515", "516", "517", "518", "519", "588", "159")
_SYMBOL_RE = re.compile(r"^(?:(SH|SZ)[.]?)?(\d{6})(?:[.](SH|SZ))?$", re.IGNORECASE)


def _split_symbol(symbol: str) -> tuple[str, str | None]:
    raw = str(symbol or "").strip().upper().replace(" ", "")
    match = _SYMBOL_RE.match(raw)
    if not match:
        raise ValueError(f"Unsupported symbol format: {symbol!r}")
    prefix_market, code, suffix_market = match.groups()
    market = suffix_market or prefix_market
    return code, market.upper() if market else None


def detect_market(symbol: str) -> str:
    """Detect ``SH`` or ``SZ`` from common A-share/ETF symbol formats."""

    code, market = _split_symbol(symbol)
    if market in {"SH", "SZ"}:
        return market
    if code.startswith(_SH_PREFIXES):
        return "SH"
    if code.startswith(_SZ_PREFIXES):
        return "SZ"
    raise ValueError(f"Cannot detect market for symbol: {symbol!r}")


def normalize_symbol(symbol: str) -> str:
    """Normalize common Chinese market symbol formats to ``510300.SH`` style."""

    code, _market = _split_symbol(symbol)
    return f"{code}.{detect_market(symbol)}"


def is_a_share_symbol(symbol: str) -> bool:
    """Return whether a symbol can be normalized as a Shanghai/Shenzhen code."""

    try:
        normalize_symbol(symbol)
    except ValueError:
        return False
    return True


def is_etf_symbol(symbol: str) -> bool:
    """Return whether a normalized or raw symbol looks like an exchange ETF."""

    try:
        code = normalize_symbol(symbol).split(".", 1)[0]
    except ValueError:
        return False
    return code.startswith(_ETF_PREFIXES)
