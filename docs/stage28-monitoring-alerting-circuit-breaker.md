# 阶段二十八：异常监控、告警、熔断

## 阶段二十八目标

阶段二十八的目标是在既有 dry-run / paper pipeline 之上补齐一层**只观察、不交易**的 Monitoring Layer，用于统一生成监控事件、dry-run 告警文件、熔断建议和 Markdown/JSON 报告。当前阶段只做本地监控与本地报告，不接实盘，不调用 QMT 交易接口，不调用 `xttrader`，不下单。

## 为什么需要异常监控、告警、熔断

量化交易流水线即使处于 dry-run / paper 模式，也可能出现数据质量下降、缓存缺失、策略信号异常、风险拒单激增、回测回撤超阈值、调度失败等问题。阶段二十八通过监控层把这些异常统一表达为结构化事件，并给出是否需要暂停后续自动化动作的熔断建议。

该能力的核心价值：

- 在进入更复杂的 Agent Research Layer 前，先保证 pipeline 可被观察、可审计、可解释。
- 将 DATA、QUALITY、RISK、SCHEDULER 等异常统一沉淀到 MonitoringReport。
- 通过 dry-run alert 验证告警链路和报告格式，而不真实发送通知。
- 用 Circuit Breaker Decision 明确区分继续观察、人工复核、暂停自动化动作。

## 核心模型

### MonitoringEvent

`MonitoringEvent` 是单条监控事件，表示一次检查发现的事实或异常。典型字段包括：

- `name`：事件名称，例如 `data_quality_warning`、`risk_reject_spike`。
- `severity`：告警等级，取值为 `INFO`、`WARNING`、`ERROR`、`CRITICAL`。
- `message`：面向人类的说明。
- `metric` / `value` / `threshold`：可选的指标名、实际值、阈值。
- `category`：监控类别，例如 `QUALITY`、`RISK`、`SCHEDULER`。

### Alert

`Alert` 是由非 INFO 级别事件生成的 dry-run 告警载荷。当前阶段只写本地 JSON 文件，字段中会明确包含：

- `dry_run: true`
- `channel: local_file`
- `real_notification_sent: false`

这意味着告警链路可被测试，但不会触达邮件、Telegram、企业微信或其他真实通知渠道。

### CircuitBreakerDecision

`CircuitBreakerDecision` 是监控后的熔断建议，包含：

- `state`：`OPEN`、`HALF_OPEN` 或 `CLOSED`。
- `triggered`：是否触发阻断建议。
- `reason`：触发原因或继续运行原因。
- `max_severity`：本轮监控最高等级。
- `dry_run_only`：当前阶段始终为 true。

### MonitoringReport

`MonitoringReport` 是阶段二十八的最终输出对象，聚合本轮 run 的事件、dry-run alert、最高等级、熔断结果、元数据等信息。它可被写出为 Markdown 和 JSON，用于人工复核、CI 检查或后续调度记录。

## 监控类别说明

- `DATA`：数据源、fallback/mock 数据路径、数据加载链路。
- `CACHE`：本地缓存命中率、缓存缺失、缓存过期。
- `QUALITY`：数据质量等级、覆盖率、字段完整性。
- `SIGNAL`：策略信号数量、信号异常、候选结果异常。
- `RISK`：Risk Gate 拒绝数量、风险约束触发。
- `BACKTEST`：回测指标、最大回撤、收益波动异常。
- `SCHEDULER`：Windows Task / scheduled pipeline 退出码和调度状态。
- `APPROVAL`：人工审批请求状态、过期、拒绝或缺失。
- `PAPER`：纸面交易状态、paper 账户模拟结果。
- `SYSTEM`：监控自身启动、报告生成、文件写入等系统级事件。

## 告警等级说明

- `INFO`：正常信息，不生成 dry-run alert 文件。
- `WARNING`：需要关注，但通常不直接触发 OPEN 熔断。
- `ERROR`：错误级异常，代表需要排查；保留为后续规则扩展等级。
- `CRITICAL`：严重异常，当前实现会触发 Circuit Breaker `OPEN` 建议。

## dry-run alert 说明

阶段二十八只支持 dry-run alert。开启 dry-run alert 后，监控会把 WARNING / ERROR / CRITICAL 事件写入本地 JSON 文件。该文件用于验证告警内容、路径和审计记录，不会真实发送邮件、Telegram、企业微信，也不会调用任何外部通知 API。

示例输出目录：

```text
monitoring_reports/alerts/
```

## Circuit Breaker 状态说明

- `OPEN`：发现 CRITICAL 事件，建议暂停后续自动化动作，必须人工复核。当前阶段只是建议，不会调用交易接口。
- `HALF_OPEN`：发现 WARNING 或 ERROR 事件，建议人工复核后再判断是否恢复。
- `CLOSED`：未发现阻断性异常，可继续保持 dry-run / paper 观察。

## `run_monitoring_check.py` 使用方式

直接运行阶段二十八监控脚本：

```bash
python scripts/run_monitoring_check.py \
  --output monitoring_reports/monitoring.md \
  --json-output monitoring_reports/monitoring.json \
  --alert-output-dir monitoring_reports/alerts \
  --quality-level LOW \
  --fallback-used \
  --risk-reject-count 3 \
  --max-drawdown -0.12
```

常用参数：

- `--output`：Markdown 报告路径。
- `--json-output`：JSON 报告路径。
- `--alert-output-dir`：dry-run alert 本地 JSON 输出目录。
- `--quality-level`：数据质量等级，例如 `UNKNOWN`、`LOW`、`MEDIUM`、`HIGH`、`UNAVAILABLE`。
- `--fallback-used`：标记是否使用 fallback/mock 数据路径。
- `--risk-reject-count`：Risk Gate 拒绝数量。
- `--scheduler-exit-code`：调度或 pipeline 退出码。
- `--max-drawdown`：最大回撤。
- `--dry-run-alerts`：保持 dry-run alert 行为；当前阶段不真实发送通知。

## `run_daily_pipeline.py --enable-monitoring` 使用方式

在日线 dry-run pipeline 结束后追加监控：

```bash
python scripts/run_daily_pipeline.py \
  --write-reports \
  --enable-monitoring \
  --monitoring-output-dir monitoring_reports \
  --monitoring-dry-run-alerts
```

该模式会读取 pipeline 结果中的数据源质量、fallback 状态、Risk Gate 拒绝数量、回测最大回撤等信息，生成 `monitoring.md`、`monitoring.json` 和可选 dry-run alert 文件。

## scheduled pipeline monitoring 参数说明

scheduled pipeline 可透传监控参数：

```bash
python scripts/run_scheduled_daily_pipeline.py \
  --enable-monitoring \
  --monitoring-output-dir monitoring_reports \
  --monitoring-dry-run-alerts
```

参数含义：

- `--enable-monitoring`：在 scheduled daily pipeline 中启用阶段二十八监控。
- `--monitoring-output-dir`：监控报告输出目录，默认 `monitoring_reports`。
- `--monitoring-dry-run-alerts`：生成本地 dry-run alert 文件。

通过 Windows Task 注册脚本生成任务命令时，也可以使用同名参数让任务命令包含监控选项。

## 当前阶段安全边界

阶段二十八只补齐监控、告警模拟和熔断建议，不做任何真实交易动作：

- 不真实发送通知。
- 不调用 QMT 交易接口。
- 不调用 `xttrader`。
- 不下单。
- 不查询真实资金、持仓、订单、成交。
- 不修改 `scripts/sync_all.ps1`。

## 阶段二十八通过后的下一阶段计划

阶段二十八通过后，下一阶段计划为：**阶段二十九 Agent Research Layer**。

阶段二十九将基于已经具备的缓存数据、报告、监控和熔断结果，构建更高层的 Agent Research Layer，用于研究辅助、候选解释、策略复盘和人类可审计的研究工作流。阶段二十九仍应优先保持 dry-run / paper 安全边界，避免直接连接实盘交易动作。
