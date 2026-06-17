"""Runtime settings loaded from environment variables only."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable with common on/off spellings."""

    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return default


def _env_float(name: str, default: float) -> float:
    """Read a float environment variable, falling back on invalid input."""

    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value.strip())
    except ValueError:
        return default


def _env_symbol_set(name: str) -> set[str]:
    """Read a comma-separated symbol list into normalized symbol strings."""

    value = os.getenv(name, "")
    return {item.strip().upper() for item in value.split(",") if item.strip()}


@dataclass(frozen=True, slots=True)
class Settings:
    """Safe runtime configuration for the application.

    No real keys, tokens, passwords, account ids, or local QMT paths are stored
    in source code; every value comes from environment variables.
    """

    live_trading_enabled: bool = False
    dry_run: bool = True
    qmt_account_id: str = ""
    qmt_userdata_path: str = ""
    llm_api_key: str = ""
    openai_api_key: str = ""
    tushare_token: str = ""
    akshare_enabled: bool = True
    max_position_pct: float = 0.2
    require_live_confirm: bool = True
    live_confirm_token: str = ""
    symbol_blacklist: set[str] = field(default_factory=set)
    allow_stock_buy: bool = True
    allow_etf_buy: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return settings from environment variables without hard-coded secrets."""

    return Settings(
        live_trading_enabled=_env_bool("LIVE_TRADING_ENABLED", False),
        dry_run=_env_bool("DRY_RUN", True),
        qmt_account_id=os.getenv("QMT_ACCOUNT_ID", ""),
        qmt_userdata_path=os.getenv("QMT_USERDATA_PATH", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        tushare_token=os.getenv("TUSHARE_TOKEN", ""),
        akshare_enabled=_env_bool("AKSHARE_ENABLED", True),
        max_position_pct=_env_float("MAX_POSITION_PCT", 0.2),
        require_live_confirm=_env_bool("REQUIRE_LIVE_CONFIRM", True),
        live_confirm_token=os.getenv("LIVE_CONFIRM_TOKEN", ""),
        symbol_blacklist=_env_symbol_set("SYMBOL_BLACKLIST"),
        allow_stock_buy=_env_bool("ALLOW_STOCK_BUY", True),
        allow_etf_buy=_env_bool("ALLOW_ETF_BUY", True),
    )
