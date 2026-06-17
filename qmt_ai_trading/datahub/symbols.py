"""Symbol normalization placeholders."""

from __future__ import annotations


def normalize_symbol(symbol: str) -> str:
    """Return a stripped symbol for now.

    TODO: Define one canonical A-share/ETF symbol format and adapters for QMT,
    AkShare, Tushare, and other data providers without changing existing data
    retrieval code.
    """

    return symbol.strip().upper()
