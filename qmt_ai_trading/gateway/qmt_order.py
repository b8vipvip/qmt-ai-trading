"""Standard QMT order gateway guarded by the project Risk Gate.

This module deliberately keeps real QMT order submission behind a disabled
adapter placeholder. Importing it never connects to QMT and never submits orders.
"""

from __future__ import annotations

from dataclasses import asdict

from qmt_ai_trading.common.types import OrderResult, TradeIntent
from qmt_ai_trading.config.settings import get_settings
from qmt_ai_trading.risk.trade_validator import validate_trade_intent


def place_order(intent: TradeIntent) -> OrderResult:
    """Validate and place a trade intent through the standardized gateway.

    Dry-run intents return a simulated success after validation. Non-dry-run
    intents are refused unless live trading is explicitly enabled, and even then
    the live QMT adapter is intentionally left unimplemented for this stage.
    """

    decision = validate_trade_intent(intent)
    decision_raw = asdict(decision)

    if not decision.allowed:
        return OrderResult(success=False, message="; ".join(decision.reasons), raw=decision_raw)

    if intent.dry_run:
        return OrderResult(
            success=True,
            order_id="DRY-RUN",
            message="dry-run order accepted by QMT gateway simulation",
            raw={"risk_decision": decision_raw, "intent": asdict(intent)},
        )

    settings = get_settings()
    if not settings.live_trading_enabled:
        return OrderResult(
            success=False,
            message="live trading is disabled by LIVE_TRADING_ENABLED",
            raw=decision_raw,
        )

    # TODO(stage2): connect this to a reviewed QMT order adapter only after the
    # full Risk Gate and manual live-trading controls are finalized. Do not call
    # the real broker order API directly from strategy or agent code.
    return OrderResult(
        success=False,
        message="live QMT order adapter is not implemented",
        raw=decision_raw,
    )


class QmtOrderGateway:
    """Backward-compatible object wrapper around :func:`place_order`."""

    def submit_order(self, intent: TradeIntent) -> OrderResult:
        """Submit an order intent through the standardized order gateway."""

        return place_order(intent)
