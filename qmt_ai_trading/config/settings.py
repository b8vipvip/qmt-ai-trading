"""Runtime settings loaded from environment variables only."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    """Safe runtime configuration for the application."""

    live_trading_enabled: bool = False
    dry_run: bool = True
    qmt_account_id: str = ""
    qmt_userdata_path: str = ""
    openai_api_key: str = ""
    llm_api_key: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return settings from environment variables without hard-coded secrets."""

    return Settings(
        live_trading_enabled=_env_bool("LIVE_TRADING_ENABLED", False),
        dry_run=_env_bool("DRY_RUN", True),
        qmt_account_id=os.getenv("QMT_ACCOUNT_ID", ""),
        qmt_userdata_path=os.getenv("QMT_USERDATA_PATH", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
    )
