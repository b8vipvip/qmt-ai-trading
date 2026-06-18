# 阶段三十四：真实通知 dry-run 接入准备

## 阶段三十四目标
建立真实通知 dry-run 接入准备层，为 EMAIL / TELEGRAM / WECHAT 等真实通道提供本地消息模型、模板、delivery plan、发送前审计、敏感信息脱敏和本地预览。

## 为什么需要真实通知 dry-run 接入准备
在 Monitoring、Agent Research、Data Quality Tracking、Live Gray Readiness、Dashboard 已具备后，需要先验证通知内容、目的地脱敏、审计报告与计划任务参数，而不是直接开启真实通知。

## 核心模型
- `NotificationMessage`：统一通知消息，包含 subject、body、source、run_id 和 metadata。
- `NotificationRecipient`：通知接收人，仅保存 masked destination。
- `NotificationDeliveryPlan`：发送计划，默认 `dry_run=True`、`real_send_enabled=False`、`external_network_enabled=False`。
- `NotificationAuditResult`：发送前安全审计结果、blocked reasons、warnings 和 safety note。
- `NotificationDryRunReport`：汇总消息、接收人、delivery plans、audit、output files 和 summary。

## 支持渠道
支持 `FILE`、`CONSOLE`、`EMAIL`、`TELEGRAM`、`WECHAT`。当前阶段 `EMAIL` / `TELEGRAM` / `WECHAT` 只能生成 dry-run / suppressed plan，不允许真实发送。

## CLI 使用方式
```powershell
py scripts/run_notification_dry_run.py --channels FILE,CONSOLE,EMAIL,TELEGRAM,WECHAT --recipients "ops@example.com,+8613800000000,telegram:123456,wechat:https://example.invalid/webhook" --output notification_dryrun_stage34/notification_dryrun.md --json-output notification_dryrun_stage34/notification_dryrun.json --preview-output-dir notification_dryrun_stage34/previews
```

## Daily Pipeline 使用方式
```powershell
py scripts/run_daily_pipeline.py --enable-notification-dry-run --notification-dry-run-output-dir notification_dryrun_stage34 --notification-dry-run-channels FILE,CONSOLE,EMAIL,TELEGRAM,WECHAT
```

## Scheduled Pipeline 参数
`run_scheduled_daily_pipeline.py` 和 `register_daily_pipeline_task.py` 支持 `--enable-notification-dry-run`、`--notification-dry-run-output-dir`、`--notification-dry-run-channels`；不会包含真实 token 或 real-send 参数。

## Dashboard Notification Dry Run section
Dashboard 新增只读 Notification Dry Run section，只读取本地 Markdown / JSON，文件不存在时返回 EMPTY，不读取敏感文件，不调用外部网络。

## 敏感信息脱敏
目的地和消息正文会对 email、手机号、telegram chat id、webhook URL、token/key/password/secret/account/bearer/sk- 等模式做脱敏或阻断。

## 安全边界
当前阶段不读取真实 token、不调用外部网络、不真实发送通知；不调用 QMT 交易接口、不调用 xttrader、不下单。

## 下一阶段计划
阶段三十五：小资金灰度人工流程演练。阶段三十五仍默认 dry-run，不真实下单，不调用 xttrader，不真实发送通知。
