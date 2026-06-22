# frontend_xtdata_enable_contract

```json
{
  "allow_xttrader": false,
  "apis": [
    "GET /api/v1/market/xtdata-enable/context",
    "GET /api/v1/market/xtdata-enable/request",
    "GET /api/v1/market/xtdata-enable/environment",
    "GET /api/v1/market/xtdata-enable/checklist",
    "GET /api/v1/market/xtdata-enable/audit",
    "GET /api/v1/market/xtdata-enable/decision",
    "GET /api/v1/market/xtdata-enable/report",
    "POST /api/v1/tasks/run task_id=xtdata_enable_dry_run"
  ],
  "decision": "READY_FOR_MANUAL_REVIEW",
  "dry_run": true,
  "enable_xtdata": false,
  "manual_confirmation_completed": false,
  "mini_qmt_connected": false,
  "page": "xtdata 启用确认",
  "read_only": true,
  "real_market_data": false,
  "requires_human_confirmation": true,
  "safety_boundary": "Stage86 only creates dry-run reports and cannot enable live data.",
  "sections": [
    "xtdata 启用请求状态",
    "环境检测结果",
    "人工确认 checklist",
    "配置审计表",
    "安全阻断原因",
    "sandbox fallback 状态",
    "下一阶段计划",
    "安全边界说明"
  ],
  "xtdata_imported": false
}
```
