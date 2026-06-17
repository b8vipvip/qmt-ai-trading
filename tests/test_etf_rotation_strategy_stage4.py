from unittest import mock

from qmt_ai_trading.risk.trade_validator import validate_trade_intent
from qmt_ai_trading.strategies.etf_rotation import (
    ETFCandidate,
    generate_etf_rotation_intents,
    generate_etf_rotation_signal,
    select_top_etfs,
)


def test_no_candidates_returns_hold_or_empty_intents():
    intent = generate_etf_rotation_signal([])
    assert intent.side == "HOLD"
    assert "no ETF candidates" in intent.reason or "no eligible" in intent.reason
    assert generate_etf_rotation_intents([]) == []


def test_single_candidate_generates_dry_run_buy_intent():
    intent = generate_etf_rotation_signal([ETFCandidate(symbol="510300.SH", score=88, last_price=4.0)])
    assert intent.side == "BUY"
    assert intent.symbol == "510300.SH"
    assert intent.dry_run is True


def test_buy_quantity_is_100_share_multiple():
    intent = generate_etf_rotation_signal([ETFCandidate(symbol="510300.SH", score=88, last_price=4.0)])
    assert intent.quantity > 0
    assert intent.quantity % 100 == 0


def test_target_percent_not_above_max_position_pct(monkeypatch):
    monkeypatch.setenv("MAX_POSITION_PCT", "0.15")
    from qmt_ai_trading.config import settings

    settings.get_settings.cache_clear()
    intent = generate_etf_rotation_signal([ETFCandidate(symbol="510300.SH", score=88, target_percent=0.9)])
    assert intent.target_percent == 0.15
    settings.get_settings.cache_clear()


def test_source_is_etf_rotation():
    intent = generate_etf_rotation_signal([ETFCandidate(symbol="510300.SH", score=88)])
    assert intent.source == "etf_rotation"


def test_generated_intent_passes_risk_gate():
    intent = generate_etf_rotation_signal([ETFCandidate(symbol="510300.SH", score=88)])
    decision = validate_trade_intent(intent)
    assert decision.allowed, decision.reasons


def test_low_score_candidate_not_selected():
    decision = select_top_etfs([ETFCandidate(symbol="510300.SH", score=10)], min_score=60)
    assert decision.selected == []
    assert decision.rejected[0].eligible is False


def test_multiple_candidates_sorted_by_score_select_top():
    intents = generate_etf_rotation_intents([
        ETFCandidate(symbol="510300.SH", score=70),
        ETFCandidate(symbol="159915.SZ", score=95),
        ETFCandidate(symbol="588000.SH", score=80),
    ], top_n=2)
    assert [item.symbol for item in intents] == ["159915.SZ", "588000.SH"]


def test_dry_run_default_true():
    intent = generate_etf_rotation_signal([ETFCandidate(symbol="510300.SH", score=88)])
    assert intent.dry_run is True


def test_strategy_does_not_call_qmt_order_place_order():
    with mock.patch("qmt_ai_trading.gateway.qmt_order.place_order") as place_order:
        generate_etf_rotation_signal([ETFCandidate(symbol="510300.SH", score=88)])
        generate_etf_rotation_intents([ETFCandidate(symbol="510300.SH", score=88)])
    place_order.assert_not_called()
