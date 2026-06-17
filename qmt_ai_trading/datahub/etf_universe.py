"""Default ETF universe for Data Hub.

The built-in list is a small offline candidate pool for examples/tests only and
is not investment advice. Future adapters may load QMT local data, AkShare,
Tushare, or BaoStock behind the same contract.
"""

from __future__ import annotations

from qmt_ai_trading.datahub.models import ETFUniverseItem
from qmt_ai_trading.datahub.symbols import normalize_symbol

_DEFAULT_ETFS = (
    ("510300.SH", "沪深300ETF", "宽基ETF"),
    ("510500.SH", "中证500ETF", "宽基ETF"),
    ("159915.SZ", "创业板ETF", "宽基ETF"),
    ("512100.SH", "中证1000ETF", "宽基ETF"),
    ("588000.SH", "科创50ETF", "宽基ETF"),
)


def get_default_etf_universe() -> list[ETFUniverseItem]:
    """Return the offline default ETF universe candidate pool."""

    return [
        ETFUniverseItem(symbol=normalize_symbol(symbol), name=name, category=category, source="datahub_default")
        for symbol, name, category in _DEFAULT_ETFS
    ]
