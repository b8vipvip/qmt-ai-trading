from qmt_ai_trading.trading_gateway import XtTraderBoundaryConfig

def test_default_config_disabled():
    cfg = XtTraderBoundaryConfig().to_dict()
    assert cfg["enabled"] is False
    assert cfg["dry_run"] is True
    assert cfg["read_only"] is True
    assert cfg["allow_import_xttrader"] is False
    assert cfg["allow_order_submit"] is False
    assert cfg["allow_account_query"] is False
    assert cfg["requires_human_approval"] is True
