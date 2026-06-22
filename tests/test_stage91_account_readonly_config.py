from qmt_ai_trading.trading_gateway.account_readonly_config import default_account_readonly_config

def test_stage91_default_config_disabled():
    cfg = default_account_readonly_config().to_dict()
    assert cfg == {
        "enabled": False, "dry_run": True, "read_only": True,
        "allow_import_xttrader": False, "allow_create_xtquant_trader": False, "allow_connect_trade_session": False,
        "allow_account_query": False, "allow_position_query": False, "allow_order_query": False, "allow_trade_query": False,
        "allow_order_submit": False, "allow_order_cancel": False,
        "requires_human_approval": True, "manual_confirmation_completed": False,
        "mask_account_required": True, "rate_limit_required": True, "max_queries_per_minute": 3,
        "allow_auto_refresh": False, "notes": "Stage91 account readonly boundary; order submit disabled",
    }
