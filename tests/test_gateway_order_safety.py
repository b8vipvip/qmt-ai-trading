from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.config.settings import get_settings
from qmt_ai_trading.gateway.qmt_order import place_order


def teardown_function():
    get_settings.cache_clear()


def test_dry_run_trade_intent_returns_simulated_success(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "0")
    get_settings.cache_clear()

    result = place_order(TradeIntent(symbol="159915.SZ", side="BUY", quantity=100, dry_run=True))

    assert result.success is True
    assert result.order_id == "DRY-RUN"


def test_live_trade_rejected_when_live_trading_disabled(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "0")
    get_settings.cache_clear()

    result = place_order(TradeIntent(symbol="159915.SZ", side="BUY", quantity=100, dry_run=False))

    assert result.success is False
    assert "live trading is disabled" in result.message


def test_buy_quantity_must_be_multiple_of_100(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "0")
    get_settings.cache_clear()

    result = place_order(TradeIntent(symbol="159915.SZ", side="BUY", quantity=101, dry_run=True))

    assert result.success is False
    assert "multiple of 100" in result.message
