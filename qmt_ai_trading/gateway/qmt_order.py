"""QMT order gateway shell with live-trading safety defaults."""

from __future__ import annotations

from qmt_ai_trading.common.types import OrderResult, TradeIntent
from qmt_ai_trading.config.settings import get_settings
from qmt_ai_trading.risk.trade_validator import validate_trade_intent


class QmtOrderGateway:
    """Order interface placeholder guarded by settings and risk validation."""

    def submit_order(self, intent: TradeIntent) -> OrderResult:
        """Submit an order only after baseline safety checks.

        If LIVE_TRADING_ENABLED is not true, real order submission is forbidden.
        Dry-run requests return a simulated success result without calling QMT.
        """

        decision = validate_trade_intent(intent)
        if not decision.allowed:
            return OrderResult(False, message="; ".join(decision.reasons), raw=decision)

        settings = get_settings()
        if intent.dry_run:
            return OrderResult(True, order_id="DRY-RUN", message="dry-run order accepted", raw=decision)

        if not settings.live_trading_enabled:
            return OrderResult(False, message="live trading is disabled", raw=decision)

        # TODO: Call the existing QMT order implementation only after full Risk Gate approval.
        return OrderResult(False, message="live QMT order adapter is not implemented", raw=decision)
