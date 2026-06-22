from qmt_ai_trading.console_api.api_server import _account_readonly_response

ENABLED_QS = {
    "enable_account_readonly": ["true"],
    "allow_import_xttrader": ["true"],
    "allow_connect_trade_session": ["true"],
    "allow_account_query": ["true"],
    "allow_position_query": ["true"],
    "manual_confirmed": ["true"],
    "read_only": ["true"],
    "dry_run": ["true"],
    "allow_order_submit": ["false"],
    "allow_order_cancel": ["false"],
}

def test_account_readonly_api_default_disabled():
    payload = _account_readonly_response({}, "status")
    assert payload["ok"] is True
    assert payload["enabled"] is False
    assert payload["account_query_enabled"] is False
    assert payload["position_query_enabled"] is False
    assert payload["order_submit_enabled"] is False
    assert payload["real_order_submitted"] is False

def test_account_readonly_api_enabled_params_use_readonly_provider():
    payload = _account_readonly_response(ENABLED_QS, "status")
    assert payload["enabled"] is True
    assert payload["account_query_enabled"] is True
    assert payload["position_query_enabled"] is True
    assert payload["manual_confirmation_completed"] is True
    assert payload["safety_status"] == "READONLY_ENABLED"

def test_account_readonly_api_forces_order_permissions_false():
    qs = {**ENABLED_QS, "allow_order_submit": ["true"], "allow_order_cancel": ["true"]}
    payload = _account_readonly_response(qs, "status")
    assert payload["order_submit_enabled"] is False
    assert payload["order_cancel_enabled"] is False
    assert payload["real_order_submitted"] is False
    assert payload["warnings"]
