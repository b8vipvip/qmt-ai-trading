# workflow_dry_run_check

```json
{
  "stage": "Stage87",
  "task_id": "workflow_dry_run_check",
  "status": "SUCCESS",
  "sequence": [
    "GET /api/v1/market/xtdata-live/status",
    "GET /api/v1/datahub/status",
    "POST /api/v1/tasks/run factor_research_dry_run",
    "POST /api/v1/tasks/run agent_research_dry_run",
    "POST /api/v1/tasks/run factor_strategy_dry_run",
    "POST /api/v1/tasks/run risk_gate_dry_run",
    "GET /api/v1/approval/status",
    "GET /api/v1/paper-trading/status"
  ],
  "message": "dry-run only; no orders submitted",
  "dry_run": true,
  "read_only": true,
  "not_live_trading": true,
  "no_order_submitted": true,
  "no_xttrader": true,
  "no_account_query": true
}
```
