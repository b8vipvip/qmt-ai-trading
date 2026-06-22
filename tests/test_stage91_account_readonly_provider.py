from qmt_ai_trading.trading_gateway.account_readonly_config import AccountReadonlyConfig
from qmt_ai_trading.trading_gateway.account_readonly_provider import AccountReadonlyProvider

class FakeTrader:
    def query_stock_asset(self):
        return {"account_id":"1234567890","cash":100}
    def query_stock_positions(self):
        return [{"account_id":"1234567890","symbol":"510300.SH","volume":100}]

def test_provider_default_disabled_blocks_queries():
    p = AccountReadonlyProvider(AccountReadonlyConfig())
    assert p.get_status()["account_query_enabled"] is False
    assert p.query_account_asset()["query_attempted"] is False

def test_provider_manual_readonly_masks_real_adapter_data():
    cfg = AccountReadonlyConfig(enabled=True, manual_confirmation_completed=True, allow_account_query=True, allow_position_query=True)
    p = AccountReadonlyProvider(cfg, trader=FakeTrader())
    asset = p.query_account_asset()
    pos = p.query_positions()
    assert asset["asset"]["account_id"] == "12****90"
    assert pos["positions"][0]["account_id"] == "12****90"
    assert asset["order_submit_enabled"] is False
    assert pos["real_order_submitted"] is False
