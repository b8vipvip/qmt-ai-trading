# frontend_market_contract

```json
{
  "apis": [
    "GET /api/v1/market/sandbox/context",
    "GET /api/v1/market/sandbox/symbols",
    "GET /api/v1/market/sandbox/snapshots",
    "GET /api/v1/market/sandbox/bars",
    "GET /api/v1/market/sandbox/replay/latest",
    "GET /api/v1/market/sandbox/quality/latest",
    "GET /api/v1/market/sandbox/report/latest",
    "POST /api/v1/tasks/run task_id=market_replay_sandbox"
  ],
  "mock_data": true,
  "no_order_submitted": true,
  "no_qmt_trader_api": true,
  "not_live_trading": true,
  "page": "行情回放",
  "read_only": true,
  "recorded_data": false,
  "sandbox": true,
  "sections": [
    "Sandbox 行情网关状态",
    "Provider 类型显示",
    "标的列表",
    "行情快照表",
    "K线数据表",
    "Replay Bus 状态",
    "Replay Event 时间线",
    "数据质量报告",
    "安全边界说明",
    "下一阶段真实 xtdata 接入边界说明"
  ]
}
```
