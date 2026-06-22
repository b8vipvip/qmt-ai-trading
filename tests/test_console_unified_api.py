from qmt_ai_trading.console_api.routes import ROUTES

def test_required_routes_not_backend_missing():
    for path in ['/api/v1/datahub/status','/api/v1/approval/status','/api/v1/console/bootstrap']:
        data=ROUTES[path]()
        assert data['ok'] is True
        assert data.get('status') != 'BACKEND_MISSING'
        assert 'BACKEND_MISSING' not in repr(data)

def test_all_required_get_routes_registered():
    required=['/api/v1/workflow/status','/api/v1/workflow/feature-matrix','/api/v1/datahub/symbols','/api/v1/research/context','/api/v1/strategy/trade-intents/latest','/api/v1/risk/report/latest','/api/v1/agents/report/latest','/api/v1/paper-trading/pnl/latest','/api/v1/monitoring/alerts/latest','/api/v1/account-readonly/positions','/api/v1/safety/status','/api/v1/live/status']
    for p in required: assert p in ROUTES
