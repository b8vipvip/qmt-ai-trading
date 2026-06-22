from qmt_ai_trading.console_api.routes import ROUTES

def test_safety_flags_on_safety_routes():
    for p in ['/api/v1/safety/status','/api/v1/live/status','/api/v1/account-readonly/status']:
        data=ROUTES[p]()
        assert data['read_only'] is True
        assert data['dry_run'] is True or data['live_disabled'] is True
        assert data['order_submit_enabled'] is False
        assert data['order_cancel_enabled'] is False
        assert data['real_order_submitted'] is False

def test_account_masked():
    data=ROUTES['/api/v1/account-readonly/diagnostics']()
    assert '***MASKED***' in repr(data)
    assert '123456789' not in repr(data)
