from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.config.settings import get_settings
from qmt_ai_trading.risk.trade_validator import validate_trade_intent


def teardown_function():
    get_settings.cache_clear()


def _decision(intent: TradeIntent):
    get_settings.cache_clear()
    return validate_trade_intent(intent)


def test_buy_100_shares_dry_run_allowed(monkeypatch):
    monkeypatch.delenv("SYMBOL_BLACKLIST", raising=False)
    decision = _decision(TradeIntent(symbol="159915.SZ", side="BUY", quantity=100, dry_run=True))

    assert decision.allowed is True


def test_buy_88_shares_rejected():
    decision = _decision(TradeIntent(symbol="159915.SZ", side="BUY", quantity=88, dry_run=True))

    assert decision.allowed is False
    assert any("multiple of 100" in reason for reason in decision.reasons)


def test_invalid_side_rejected():
    decision = _decision(TradeIntent(symbol="159915.SZ", side="INVALID", quantity=100, dry_run=True))

    assert decision.allowed is False
    assert any("side must be one of" in reason for reason in decision.reasons)


def test_empty_symbol_rejected():
    decision = _decision(TradeIntent(symbol="", side="BUY", quantity=100, dry_run=True))

    assert decision.allowed is False
    assert any("symbol cannot be empty" in reason for reason in decision.reasons)


def test_negative_target_percent_rejected():
    decision = _decision(
        TradeIntent(symbol="159915.SZ", side="BUY", quantity=100, target_percent=-0.01, dry_run=True)
    )

    assert decision.allowed is False
    assert any("target_percent cannot be negative" in reason for reason in decision.reasons)


def test_target_percent_above_max_position_pct_rejected(monkeypatch):
    monkeypatch.setenv("MAX_POSITION_PCT", "0.2")
    decision = _decision(
        TradeIntent(symbol="159915.SZ", side="BUY", quantity=100, target_percent=0.21, dry_run=True)
    )

    assert decision.allowed is False
    assert any("exceeds max position pct" in reason for reason in decision.reasons)


def test_live_trade_rejected_when_live_trading_disabled_by_default(monkeypatch):
    monkeypatch.delenv("LIVE_TRADING_ENABLED", raising=False)
    decision = _decision(TradeIntent(symbol="159915.SZ", side="BUY", quantity=100, dry_run=False))

    assert decision.allowed is False
    assert any("live trading is disabled" in reason for reason in decision.reasons)


def test_blacklisted_symbol_rejected(monkeypatch):
    monkeypatch.setenv("SYMBOL_BLACKLIST", "159915.SZ, 600000.SH")
    decision = _decision(TradeIntent(symbol="159915.SZ", side="BUY", quantity=100, dry_run=True))

    assert decision.allowed is False
    assert any("SYMBOL_BLACKLIST" in reason for reason in decision.reasons)


def test_hold_allows_zero_quantity():
    decision = _decision(TradeIntent(symbol="159915.SZ", side="HOLD", quantity=0, dry_run=True))

    assert decision.allowed is True


def test_sell_does_not_require_lot_size_but_rejects_negative_quantity():
    odd_lot = _decision(TradeIntent(symbol="159915.SZ", side="SELL", quantity=88, dry_run=True))
    negative = _decision(TradeIntent(symbol="159915.SZ", side="SELL", quantity=-1, dry_run=True))

    assert odd_lot.allowed is True
    assert negative.allowed is False
    assert any("quantity cannot be negative" in reason for reason in negative.reasons)
