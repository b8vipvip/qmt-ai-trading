# Stage 9: Signal Pipeline / Daily Runner 标准化

## Signal Pipeline 职责

Stage 9 新增轻量级 Signal Pipeline，用于编排 Data Hub、Research、Model Lab、ETF Strategy、Risk Gate、Backtest / Shadow Replay 的每日 dry-run / shadow 流程。Pipeline 只负责流程编排和结构化结果汇总，不直接实盘下单，不连接真实 QMT 下单接口。

## Daily Runner 职责

Daily Runner 提供可由命令行触发的每日运行入口：

- 构建 `PipelineContext`。
- 加载 Data Hub 默认 ETF universe 或用户指定 ETF symbols。
- 生成 `ETFCandidate`。
- 生成 dry-run `TradeIntent`。
- 对所有 `TradeIntent` 调用 Risk Gate 校验。
- 执行模拟 Backtest / Shadow Replay。
- 输出 `PipelineResult` 和可读文本日报。

## 输入

当前输入保持轻量、离线和可测试：

- ETF universe：默认使用 `qmt_ai_trading.datahub.etf_universe.get_default_etf_universe()`。
- Data Hub：作为 universe 和未来行情 adapter 的统一入口。
- Research：后续可传入 `ResearchScore` 或评分映射，再转换为 ETF 候选。
- Model Lab：后续可把模型预测转换为 ResearchScore，再进入 ETF Strategy。

当前阶段允许后续接 QMT 行情 adapter，但不强依赖真实 QMT 行情。

## 输出

Pipeline 输出：

- `PipelineResult`
- `PipelineStepResult` 列表
- research scores / candidates / trade intents / risk decisions
- backtest result / shadow replay result
- 文本日报 `report_text`

日报包含 run_id、trade_date、候选、TradeIntent、RiskDecision 和 Backtest summary，并明确标注 dry-run / shadow。

## 交易安全边界

当前 Stage 9 只支持 dry-run / shadow：

- 默认 `dry_run=True`。
- 不连接真实 QMT 下单。
- 不调用 `qmt_order.place_order`。
- 不写入真实订单。
- 所有 `TradeIntent` 必须经过 `validate_trade_intent`。
- 真实交易仍必须经过 Risk Gate + QMT Gateway，且不属于本阶段范围。

## 后续计划

后续可以在不破坏当前安全边界的前提下接入：

- 计划任务或 Windows Task Scheduler。
- UI 展示。
- 消息通知。
- 只读 QMT 行情 adapter。
- 更完整的 Research / Model Lab scoring 输入。
