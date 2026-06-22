from qmt_ai_trading.console_api.routes import ROUTES
CRITICAL=['/api/v1/console/bootstrap','/api/v1/workflow/status','/api/v1/workflow/feature-matrix','/api/v1/datahub/status','/api/v1/datahub/symbols','/api/v1/datahub/cache/status','/api/v1/datahub/market/latest','/api/v1/research/context','/api/v1/research/factors/latest','/api/v1/research/candidates/latest','/api/v1/strategy/context','/api/v1/strategy/signals/latest','/api/v1/strategy/trade-intents/latest','/api/v1/risk/context','/api/v1/risk/decisions/latest','/api/v1/risk/report/latest','/api/v1/agents/context','/api/v1/agents/report/latest','/api/v1/backtest/shadow-replay/latest','/api/v1/paper-trading/status','/api/v1/paper-trading/orders/latest','/api/v1/paper-trading/positions/latest','/api/v1/paper-trading/pnl/latest','/api/v1/monitoring/context','/api/v1/monitoring/alerts/latest','/api/v1/monitoring/circuit-breaker/latest','/api/v1/approval/status','/api/v1/approval/requests/latest','/api/v1/account-readonly/status','/api/v1/account-readonly/diagnostics','/api/v1/account-readonly/asset','/api/v1/account-readonly/positions','/api/v1/safety/status','/api/v1/live/status']
def test_all_critical_routes_have_safety_and_no_backend_missing():
    for path in CRITICAL:
        assert path in ROUTES
        data=ROUTES[path]()
        assert data['read_only'] is True and data['dry_run'] is True and data['live_disabled'] is True
        assert data['no_order_submitted'] is True and data['requires_human_approval'] is True
        assert data['order_submit_enabled'] is False and data['real_order_submitted'] is False
        assert 'BACKEND_MISSING' not in str(data)
