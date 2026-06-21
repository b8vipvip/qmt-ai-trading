# Performance Metrics

dry_run=true
not_live_trading=true
research_only=true
fallback_used=true
mock_data=true

该结果仅用于前端联调和研究展示，不能作为实盘依据。

```json
{
  "total_return": 0.012,
  "annualized_return": 0.144,
  "max_drawdown": 0.025,
  "volatility": 0.0,
  "sharpe_like": 1.2,
  "win_rate": 1.0,
  "trade_count": 1,
  "turnover": 0.1,
  "avg_holding_days": 5.0,
  "risk_rejected_count": 0,
  "approved_dry_run_count": 0,
  "data_quality": "fallback_safe",
  "dry_run": true,
  "not_live_trading": true,
  "research_only": true,
  "no_order_submitted": true,
  "no_qmt_trader_api": true,
  "requires_risk_gate": true,
  "requires_human_approval": true,
  "fallback_used": true,
  "mock_data": true,
  "backtest_mode": "mock_shadow",
  "disclaimer": "该结果仅用于前端联调和研究展示，不能作为实盘依据。",
  "unsafe": false,
  "forbidden_terms": []
}
```
