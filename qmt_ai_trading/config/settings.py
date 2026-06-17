"""Runtime settings loaded from environment variables only."""

from __future__ import annotations

import os
from dataclasses import dataclass
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
    )
