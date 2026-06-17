"""Live-trading protection checks for the final pre-order gate."""

from __future__ import annotations

from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.config.settings import Settings


def validate_live_gate(intent: TradeIntent, settings: Settings) -> list[str]:
    """Validate explicit live-trading controls without connecting to QMT."""

    if intent.dry_run:
        return []

    reasons: list[str] = []
    if not settings.live_trading_enabled:
        reasons.append("live trading is disabled by LIVE_TRADING_ENABLED")

    if settings.require_live_confirm and not settings.live_confirm_token:
        reasons.append("live trading requires manual confirmation token")

    # TODO(stage3): add quote/position/account-aware checks here after QMT data
    # adapters are explicitly introduced. Do not connect to QMT in this module.
    return reasons
