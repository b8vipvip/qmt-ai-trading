# frontend_xtdata_live_contract

```json
{
  "allow_order_submit": false,
  "allow_xttrader": false,
  "apis": [
    "GET /api/v1/market/xtdata-live/status",
    "GET /api/v1/market/xtdata-live/snapshots",
    "GET /api/v1/market/xtdata-live/bars",
    "GET /api/v1/market/xtdata-live/safety",
    "GET /api/v1/market/xtdata-live/report",
    "POST /api/v1/tasks/run task_id=xtdata_live_readonly_smoke"
  ],
  "no_account_query": true,
  "no_order_submitted": true,
  "no_xttrader": true,
  "page": "xtdata 只读行情",
  "read_only": true,
  "sections": [
    "xtdata 连接状态",
    "MiniQMT 状态",
    "当前 provider",
    "行情 snapshot 表格",
    "K线 bars 表格",
    "sandbox fallback 状态",
    "安全边界说明",
    "禁止交易项检查"
  ]
}
```
