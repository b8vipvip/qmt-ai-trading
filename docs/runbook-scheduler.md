# Scheduler 调度手册

## Dry-run preview
使用 `py scripts/register_daily_pipeline_task.py ...` 预览 Windows Task Scheduler 命令，默认只 preview / dry-run，不包含 `--live-enabled`。

## Scheduled runner
`py scripts/run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --data-source-mode cached_real_first --build-dashboard`

## --execute 风险提示
`--execute` 表示真正注册计划任务；注册前必须人工检查命令不含 `--live-enabled`，不含自动审批、自动 paper/live submit。

## 检查和取消
在 Windows Task Scheduler 中人工检查 Action 命令；如误注册，人工禁用或删除任务。避免误注册：先不传 `--execute`，只复制 dry-run preview。

当前阶段仍不实盘、不调用 QMT 交易接口、不调用 xttrader、不查询真实资金/持仓/订单/成交、不真实发送通知、不自动 approve、不自动 paper submit、不自动 live submit、不真实下单。
