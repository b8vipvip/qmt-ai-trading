"""Complete stage-3 Risk Gate for structured trade intents."""

from __future__ import annotations

from qmt_ai_trading.common.types import RiskDecision, TradeIntent
from qmt_ai_trading.config.settings import get_settings
from qmt_ai_trading.risk.blacklist import validate_symbol_blacklist
from qmt_ai_trading.risk.live_gate import validate_live_gate
from qmt_ai_trading.risk.position_limit import validate_target_percent
from qmt_ai_trading.risk.rules import infer_risk_level, validate_basic_rules


def validate_trade_intent(intent: TradeIntent) -> RiskDecision:
    """Validate a trade intent before it can reach any real order gateway.

    This function is intentionally pure with respect to external systems: it
    does not connect to QMT, does not read accounts or positions, and does not
    request real-time quotes. Quote-sensitive checks such as ST, suspension, and
    limit-up/limit-down remain explicit TODOs for later data-aware stages.
    """

    settings = get_settings()
    reasons: list[str] = []

    reasons.extend(validate_basic_rules(intent))
    reasons.extend(validate_symbol_blacklist(intent.symbol, settings.symbol_blacklist))
    reasons.extend(validate_target_percent(intent.target_percent, settings.max_position_pct))

    # TODO(stage3): ST / suspended / limit-up / limit-down checks require an
    # explicit market-data snapshot input in a later stage. Do not connect to
    # live QMT行情 from Risk Gate validation.
    if not intent.dry_run:
        reasons.extend(validate_live_gate(intent, settings))

    allowed = not reasons
    live = not intent.dry_run
    return RiskDecision(
        allowed=allowed,
        reasons=reasons or [
            "dry-run trade intent allowed" if intent.dry_run else "live trade intent passed Risk Gate"
        ],
        adjusted_quantity=intent.quantity,
        risk_level=infer_risk_level(reasons, live=live),
    )
