# paper_orders

```json
{
  "dry_run": true,
  "no_account_query": true,
  "no_order_submitted": true,
  "no_xttrader": true,
  "not_live_trading": true,
  "orders": [
    {
      "dry_run": true,
      "fill_status": "FILLED",
      "intent_id": "stage88-510300.SH",
      "intent_price": 0.0,
      "no_account_query": true,
      "no_order_submitted": true,
      "no_xttrader": true,
      "not_live_trading": true,
      "order_id": "paper-stage88-510300.SH",
      "paper_order": true,
      "paper_trading": true,
      "quantity": 100,
      "read_only": true,
      "reject_reason": "",
      "requires_human_approval": true,
      "risk_decision": {
        "checks": {
          "dry_run": true,
          "etf_whitelist": true,
          "lot_size_100": true,
          "max_portfolio_weight": true,
          "max_single_notional": true,
          "max_symbol_weight": true,
          "no_account_query": true,
          "no_order_submitted": true,
          "no_xttrader": true,
          "requires_human_approval": true,
          "t_plus_1": true
        },
        "decision": "APPROVED_DRY_RUN",
        "dry_run": true,
        "intent_id": "stage88-510300.SH",
        "no_account_query": true,
        "no_order_submitted": true,
        "no_xttrader": true,
        "not_live_trading": true,
        "read_only": true,
        "reasons": [
          "dry-run only; human approval required"
        ],
        "requires_human_approval": true,
        "symbol": "510300.SH"
      },
      "shadow_trading": true,
      "side": "buy",
      "symbol": "510300.SH",
      "target_weight": 0.25
    }
  ],
  "paper_trading": true,
  "read_only": true,
  "requires_human_approval": true,
  "shadow_trading": true
}
```
