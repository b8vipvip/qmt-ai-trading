"""Baseline risk gate for structured trade intents."""

from __future__ import annotations

from qmt_ai_trading.common.types import RiskDecision, TradeIntent
from qmt_ai_trading.config.settings import get_settings

_ALLOWED_SIDES = {"BUY", "SELL", "HOLD"}


def validate_trade_intent(intent: TradeIntent) -> RiskDecision:
    """Validate a trade intent before it can reach any real order gateway."""

    reasons: list[str] = []
    side = intent.side.upper()

    if side not in _ALLOWED_SIDES:
        reasons.append("side must be one of BUY, SELL, or HOLD")

    if intent.quantity < 0:
        reasons.append("quantity cannot be negative")

    if side == "BUY" and intent.quantity > 0 and intent.quantity % 100 != 0:
        reasons.append("A-share buy quantity must be a multiple of 100 shares")

    settings = get_settings()
    if intent.dry_run:
        if reasons:
            return RiskDecision(False, reasons, intent.quantity, "MEDIUM")
        return RiskDecision(True, ["dry-run trade intent allowed"], intent.quantity, "LOW")

    if not settings.live_trading_enabled:
        reasons.append("live trading is disabled by LIVE_TRADING_ENABLED")

    allowed = not reasons
    return RiskDecision(
        allowed=allowed,
        reasons=reasons or ["live trade intent passed baseline validation"],
        adjusted_quantity=intent.quantity,
        risk_level="LOW" if allowed else "HIGH",
    )
