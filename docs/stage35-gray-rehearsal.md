# 阶段三十五：小资金灰度人工流程演练

## 阶段三十五目标
阶段三十五建立 Gray Rehearsal 小资金灰度人工流程演练层，在 dry-run / paper / local report 范围内串联信号、Risk Gate、Human Approval、Paper Trading、Monitoring、Data Quality Tracking、Agent Research、Live Gray Readiness、Notification Dry Run 与 Dashboard 证据。

## 为什么需要小资金灰度人工流程演练
在进入任何真实资金灰度前，需要先用本地文件和 mock context 演练人工复核链路，确认 Risk Gate 不能被绕过、Human Approval 不能被绕过、Live Gray Readiness 不能自动 GO、Notification Dry Run 不真实发送、Dashboard 只读且无下单入口。

## 核心模型
- `GrayRehearsalConfig`：默认 `rehearsal_dry_run=True`，记录场景、允许标的、小资金上限、单笔上限和必需环节。
- `GrayRehearsalScenarioResult`：记录每个演练场景的 decision、步骤、阻断原因、warning 和 evidence。
- `GrayRehearsalReport`：汇总所有场景、人工 checklist、summary 和 safety note；PASS/WARN 只代表演练链路可复核，不代表允许实盘。

## 场景说明
- `NORMAL_DRY_RUN`：确认全链路 dry-run、Risk Gate 与 Human Approval 必需。
- `RISK_GATE_BLOCKED`：确认 Risk Gate 阻断不能继续进入 approval/paper/live。
- `DATA_QUALITY_UNKNOWN`：确认质量 UNKNOWN 只作为本地复核 warning，不触发实盘。
- `CIRCUIT_BREAKER_OPEN`：确认 Monitoring / Circuit Breaker 可阻断推进。
- `LIVE_GRAY_NO_GO`：确认 Live Gray Readiness 只允许 NO_GO / BLOCKED / READY_FOR_MANUAL_REVIEW，不自动 GO。
- `NOTIFICATION_DRY_RUN`：确认通知只生成 dry-run plan/report，不真实发送。
- `DASHBOARD_READ_ONLY`：确认 Dashboard 只读、无订单入口。

## run_gray_rehearsal.py 使用方式
```powershell
py scripts/run_gray_rehearsal.py --output gray_rehearsal_stage35/gray_rehearsal.md --json-output gray_rehearsal_stage35/gray_rehearsal.json --allowed-symbols 510300.SH,510500.SH --max-total-capital 5000 --max-single-order-value 1000
```

## run_daily_pipeline.py --enable-gray-rehearsal 使用方式
```powershell
py scripts/run_daily_pipeline.py --enable-gray-rehearsal --gray-rehearsal-output-dir gray_rehearsal_stage35 --gray-rehearsal-allowed-symbols 510300.SH,510500.SH --gray-rehearsal-max-total-capital 5000 --gray-rehearsal-max-single-order-value 1000
```

## scheduled pipeline gray rehearsal 参数说明
`run_scheduled_daily_pipeline.py` 和 `register_daily_pipeline_task.py` 透传 `--enable-gray-rehearsal`、`--gray-rehearsal-output-dir`、`--gray-rehearsal-allowed-symbols`、`--gray-rehearsal-max-total-capital`、`--gray-rehearsal-max-single-order-value`。默认不包含 `--live-enabled` 或真实发送参数。

## Dashboard Gray Rehearsal section
Dashboard 新增只读 Gray Rehearsal section，只读取本地 Gray Rehearsal Markdown / JSON。文件不存在时返回 EMPTY，不读取敏感文件，不调用外部网络，不提供下单按钮。

## 安全边界
当前阶段不启用实盘、不调用 QMT 交易接口、不调用 xttrader、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单、不自动 approve、不自动 paper submit、不自动 live submit。

## 下一阶段计划
阶段三十六：小资金灰度准入复核 / 人工决策包。阶段三十六仍默认 dry-run，不真实下单，不调用 xttrader，不真实发送通知。
