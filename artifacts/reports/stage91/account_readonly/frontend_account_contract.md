# frontend_account_contract

```json
{
  "account_masked": true,
  "account_query_enabled": false,
  "enabled": false,
  "endpoints": [
    "/api/v1/account-readonly/status",
    "/api/v1/account-readonly/asset",
    "/api/v1/account-readonly/positions",
    "/api/v1/account-readonly/masking-report",
    "/api/v1/account-readonly/rate-limit",
    "/api/v1/account-readonly/safety",
    "/api/v1/account-readonly/report"
  ],
  "forbidden_actions_absent": true,
  "manual_confirmation_text": "我确认本次只进行账户/持仓只读查询；不下单、不自动交易；查询结果仅用于风险校验和灰度准备。",
  "menu": [
    "账户只读",
    "持仓只读"
  ],
  "mock_data": true,
  "order_cancel_enabled": false,
  "order_submit_enabled": false,
  "position_query_enabled": false,
  "read_only": true,
  "real_order_submitted": false,
  "requires_human_approval": true,
  "safety_status": "DISABLED_FOR_SAFETY",
  "status": "DISABLED"
}
```
