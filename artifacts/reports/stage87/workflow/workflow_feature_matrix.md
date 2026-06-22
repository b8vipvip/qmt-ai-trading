# workflow_feature_matrix

```json
{
  "stage": "Stage87",
  "features": [
    {
      "feature": "QMT Gateway / xtdata",
      "status": "INTERACTIVE",
      "api": "/api/v1/market/xtdata-live/status",
      "note": "readonly xtdata smoke",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "QMT Gateway / xttrader account query",
      "status": "DISABLED_FOR_SAFETY",
      "api": null,
      "note": "xttrader/account query forbidden",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "QMT Gateway / order submit",
      "status": "DISABLED_FOR_SAFETY",
      "api": null,
      "note": "order submit forbidden",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Data Hub / symbols",
      "status": "BACKEND_MISSING",
      "api": "/api/v1/datahub/symbols",
      "note": "needs readonly API",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Data Hub / market cache",
      "status": "BACKEND_MISSING",
      "api": "/api/v1/datahub/cache/status",
      "note": "needs cache API",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Data Hub / ETF universe",
      "status": "READY",
      "api": null,
      "note": "python datahub ETF universe exists; API pending",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Research / factors",
      "status": "INTERACTIVE",
      "api": "/api/v1/factor/context",
      "note": "factor dry-run API",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Research / model lab",
      "status": "STATIC_PLACEHOLDER",
      "api": null,
      "note": "model lab UI/API pending",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "TradingAgents / technical",
      "status": "INTERACTIVE",
      "api": "/api/v1/agents/report/latest",
      "note": "agent report includes technical role",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "TradingAgents / fundamental",
      "status": "INTERACTIVE",
      "api": "/api/v1/agents/report/latest",
      "note": "agent report includes fundamental role",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "TradingAgents / sentiment",
      "status": "INTERACTIVE",
      "api": "/api/v1/agents/debate/latest",
      "note": "agent debate/report",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "TradingAgents / risk",
      "status": "INTERACTIVE",
      "api": "/api/v1/agents/risk-review/latest",
      "note": "agent risk review",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "TradingAgents / portfolio manager",
      "status": "INTERACTIVE",
      "api": "/api/v1/agents/portfolio-review/latest",
      "note": "portfolio review",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Strategy Engine / ETF rotation",
      "status": "STATIC_PLACEHOLDER",
      "api": null,
      "note": "strategy API pending",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Strategy Engine / multi-factor stock",
      "status": "INTERACTIVE",
      "api": "/api/v1/strategy/signals/latest",
      "note": "factor strategy dry-run",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Strategy Engine / position sizing",
      "status": "INTERACTIVE",
      "api": "/api/v1/strategy/trade-intents/latest",
      "note": "dry-run intents",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Risk Gate / trade validator",
      "status": "INTERACTIVE",
      "api": "/api/v1/risk/decisions/latest",
      "note": "risk dry-run",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Human Approval",
      "status": "BACKEND_MISSING",
      "api": "/api/v1/approval/status",
      "note": "readonly approval API pending",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Paper Trading",
      "status": "BACKEND_MISSING",
      "api": "/api/v1/paper-trading/status",
      "note": "paper API pending",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Shadow Trading",
      "status": "BACKEND_MISSING",
      "api": "/api/v1/shadow-trading/report/latest",
      "note": "shadow API pending",
      "read_only": true,
      "no_order_submitted": true
    },
    {
      "feature": "Live Trading",
      "status": "DISABLED_FOR_SAFETY",
      "api": "/api/v1/live/status",
      "note": "disabled by default",
      "read_only": true,
      "no_order_submitted": true
    }
  ],
  "dry_run": true,
  "read_only": true,
  "not_live_trading": true,
  "no_order_submitted": true,
  "no_xttrader": true,
  "no_account_query": true
}
```
