# Shadow Replay Result

dry_run=true
not_live_trading=true
research_only=true
fallback_used=true
mock_data=true

该结果仅用于前端联调和研究展示，不能作为实盘依据。

```json
{
  "stage": "Stage82",
  "backtest_mode": "mock_shadow",
  "shadow_replay": [
    {
      "symbol": "510300.SH",
      "shadow_trade_id": "shadow-1",
      "signal": "WATCH_ONLY",
      "mock_return": 0.012,
      "max_drawdown": 0.025,
      "win": true,
      "holding_days": 5,
      "linked_trade_intent": "mock-intent-1",
      "dry_run": true,
      "not_live_trading": true,
      "research_only": true
    }
  ],
  "trade_count": 1,
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
  "disclaimer": "该结果仅用于前端联调和研究展示，不能作为实盘依据。",
  "unsafe": false,
  "forbidden_terms": []
}
```
