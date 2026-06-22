from . import workflow,datahub,research,strategy,risk,agent,paper,approval,account_readonly,market,safety,monitoring,backtest
ROUTES={
'/api/v1/console/bootstrap': workflow.bootstrap, '/api/v1/workflow/status': workflow.status, '/api/v1/workflow/feature-matrix': workflow.feature_matrix,
'/api/v1/datahub/status': datahub.status, '/api/v1/datahub/symbols': datahub.symbols, '/api/v1/datahub/cache/status': datahub.cache_status, '/api/v1/datahub/market/latest': datahub.market_latest,
'/api/v1/research/context': research.context, '/api/v1/research/factors/latest': research.factors, '/api/v1/research/candidates/latest': research.candidates,
'/api/v1/strategy/context': strategy.context, '/api/v1/strategy/signals/latest': strategy.signals, '/api/v1/strategy/trade-intents/latest': strategy.intents,
'/api/v1/risk/context': risk.context, '/api/v1/risk/decisions/latest': risk.decisions, '/api/v1/risk/report/latest': risk.report,
'/api/v1/agents/context': agent.context, '/api/v1/agents/report/latest': agent.report,
'/api/v1/backtest/shadow-replay/latest': backtest.shadow_replay,
'/api/v1/paper-trading/status': paper.status, '/api/v1/paper-trading/orders/latest': paper.orders, '/api/v1/paper-trading/positions/latest': paper.positions, '/api/v1/paper-trading/pnl/latest': paper.pnl,
'/api/v1/monitoring/context': monitoring.context, '/api/v1/monitoring/alerts/latest': monitoring.alerts, '/api/v1/monitoring/circuit-breaker/latest': monitoring.circuit,
'/api/v1/approval/status': approval.status, '/api/v1/approval/requests/latest': approval.requests,
'/api/v1/account-readonly/status': account_readonly.status, '/api/v1/account-readonly/diagnostics': account_readonly.diagnostics, '/api/v1/account-readonly/asset': account_readonly.asset, '/api/v1/account-readonly/positions': account_readonly.positions,
'/api/v1/safety/status': safety.status, '/api/v1/live/status': safety.live, '/api/v1/market/xtdata-live/status': market.xtdata_status,
}
