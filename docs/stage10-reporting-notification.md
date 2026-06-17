# Stage 10: Reporting / Notification 输出层标准化

## Reporting 层职责

Stage 10 新增 `qmt_ai_trading.reporting` 输出层，用于把 Stage 9 Daily Pipeline 生成的 `PipelineResult` 转换为离线报告文件。该层只消费已生成的 dry-run / shadow 结果，不连接真实 QMT，不提交订单，不改变 Strategy、Risk、Backtest 或 Research 的既有逻辑。

## Markdown / JSON / HTML 报告

报告写入函数位于 `qmt_ai_trading/reporting/writer.py`：

- `write_markdown_report(...)`：生成 `daily_report.md`，复用现有文本日报内容。
- `write_json_report(...)`：生成结构化 `daily_report.json`，包含 context、steps、candidates、trade intents、risk decisions、backtest / shadow replay 摘要和 metadata。
- `write_html_report(...)`：生成简单静态 `daily_report.html`，用于人工浏览。
- `write_pipeline_reports(...)`：一次性输出 Markdown、JSON、HTML 三种格式。

## reports/ 输出目录

默认输出目录为：

```text
reports/YYYY-MM-DD/
```

生成文件属于运行产物，已通过 `.gitignore` 忽略，不应提交到 Git 仓库。命令行也可通过 `--report-dir` 指定临时输出目录。

## 通知适配器占位

通知占位函数位于 `qmt_ai_trading/reporting/notifier.py`：

- `notify_email(...)`
- `notify_telegram(...)`
- `notify_wecom(...)`
- `notify_report(...)`

当前阶段所有通知适配器均为 dry-run placeholder，只返回 `NotificationResult`，不读取真实 Token，不连接邮件、Telegram、企业微信或其他外部通知服务。

## 安全边界

- 当前阶段全部 dry-run，不真实发送通知。
- 不包含 `.env`、Token、账号、密钥、Webhook URL 等敏感信息。
- JSON 序列化会过滤常见敏感字段名。
- 报告只用于人工复核，不是交易指令。
- 后续如接入真实通知配置，必须从环境变量读取，并继续避免在报告、日志或控制台中打印敏感值。
