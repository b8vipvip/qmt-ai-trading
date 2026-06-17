"""Pure baseline risk rules for trade intents."""

from __future__ import annotations

from qmt_ai_trading.common.types import TradeIntent

ALLOWED_SIDES = {"BUY", "SELL", "HOLD"}
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}


def normalize_side(side: str) -> str:
    """Return a normalized side string for rule checks."""

    return (side or "").strip().upper()


def validate_basic_rules(intent: TradeIntent) -> list[str]:
    """Validate dependency-free structural trading rules."""

    reasons: list[str] = []
    side = normalize_side(intent.side)

    if not (intent.symbol or "").strip():
        reasons.append("symbol cannot be empty")

    if side not in ALLOWED_SIDES:
        reasons.append("side must be one of BUY, SELL, or HOLD")

    if intent.quantity < 0:
        reasons.append("quantity cannot be negative")

    if intent.target_percent < 0:
        reasons.append("target_percent cannot be negative")

    if side == "BUY" and intent.quantity > 0 and intent.quantity % 100 != 0:
        reasons.append("A-share buy quantity must be a multiple of 100 shares")

    return reasons


def infer_risk_level(reasons: list[str], *, live: bool = False) -> str:
    """Map rule failures to a simple display-friendly risk level."""

    if not reasons:
        return "LOW"
    if live:
        return "HIGH"
    return "MEDIUM"
