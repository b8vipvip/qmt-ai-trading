# Live Gray Readiness 操作手册

## 使用方式
`py scripts/run_live_gray_readiness.py --output live_gray_reports_stage32/live_gray_readiness.md --json-output live_gray_reports_stage32/live_gray_readiness.json --allowed-symbols 510300.SH,510500.SH --max-total-capital 5000 --max-single-order-value 1000`

## 决策含义
- `NO_GO`：默认状态，live/gray 未启用或只准备不推进。
- `BLOCKED`：存在 FAIL/CRITICAL，必须阻断。
- `READY_FOR_MANUAL_REVIEW`：仅可进入人工复核候选，不代表 GO。

默认 `live_enabled=False`、`gray_enabled=False`；`--live-enabled` 默认不使用。证据要求包括 Human Approval、Risk Gate、Paper、Audit、Monitoring、Agent、Circuit Breaker、Quality、小资金上限和白名单。

当前阶段仍不实盘、不调用 QMT 交易接口、不调用 xttrader、不查询真实资金/持仓/订单/成交、不真实发送通知、不自动 approve、不自动 paper submit、不自动 live submit、不真实下单。
