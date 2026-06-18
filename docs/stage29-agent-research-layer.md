# 阶段二十九：Agent Research Layer

## 阶段二十九目标

阶段二十九在 DataHub / Research / Model Lab / Backtest / Portfolio / Monitoring 之后增加只读 Agent Research Layer，用于解释信号、总结风险、整理回测与监控结论、对比候选并生成 Human Review Checklist。

## 为什么需要 Agent Research Layer

Daily Pipeline 已经能生成候选、dry-run TradeIntent、RiskDecision、Portfolio Plan、Monitoring Report 和 Backtest 结果。Agent Research Layer 将这些只读证据汇总为可审计 Research Memo，帮助人工理解策略表现和风险状态。

## 核心模型

- `AgentResearchContext`：汇总数据源、缓存质量、候选、TradeIntent、RiskDecision、Portfolio Plan、Monitoring、Backtest 和 warnings。
- `AgentResearchMemo`：结构化 memo，包含 executive summary、signal explanation、risk summary、portfolio summary、monitoring summary、backtest summary、candidate comparison、human review checklist 和 safety note。
- `AgentActionPolicy`：默认所有 `allow_*` 均为 `False`，禁止下单、QMT access、xttrader、外部网络、真实通知、审批变更和 paper submission。

## local_rules summarizer

`local_rules` 是当前默认 deterministic summarizer。它只根据本地结构化上下文生成固定格式摘要，不调用 OpenAI、Anthropic 或任何外部 LLM API。

## external_llm_disabled

`external_llm_disabled` 模式只输出 disabled message，表示当前阶段外部 LLM 能力被策略禁用，不读取真实 key，不访问外部网络。

## Candidate comparison

候选对比按本地候选 score 排序展示 symbol、score、eligible 和 reason，仅供人工复核，不生成订单。

## Risk summary

Risk summary 汇总 Risk Gate allowed / blocked 状态。Agent 不改变 RiskDecision，不绕过 Risk Gate。

## Monitoring summary

Monitoring summary 汇总事件数、告警数和熔断建议。当前阶段不真实发送通知。

## Backtest summary

Backtest summary 汇总长期回测或 pipeline shadow replay 指标，用于复盘收益、回撤、波动和交易数量。

## Human review checklist

Checklist 固定包含 Risk Gate、Human Approval、Paper Trading、缓存质量、组合集中度和回测回撤复核项。

## run_agent_research.py 使用方式

```powershell
py scripts/run_agent_research.py --output agent_reports_stage29/agent_research.md --json-output agent_reports_stage29/agent_research.json --mode local_rules --include-monitoring --include-backtest --include-human-checklist
```

没有输入文件时脚本生成空上下文 memo 和 warning，不崩溃。

## run_daily_pipeline.py --enable-agent-research 使用方式

```powershell
py scripts/run_daily_pipeline.py --enable-agent-research --agent-research-output-dir agent_reports_stage29 --agent-research-mode local_rules
```

开启后 pipeline 完成时写出 Markdown / JSON Agent Research memo，并在 pipeline report 中加入 Agent Research 区块。

## scheduled pipeline Agent Research 参数

`run_scheduled_daily_pipeline.py` 和 `register_daily_pipeline_task.py` 支持：

- `--enable-agent-research`
- `--agent-research-output-dir`
- `--agent-research-mode local_rules`
- `--agent-include-monitoring`
- `--agent-include-backtest`
- `--agent-include-human-checklist`

## 安全边界

Agent 只读，不下单，不生成订单，不提交订单，不触发 Approval / Paper / Live，不绕过 Risk Gate / Human Approval。

当前阶段不调用外部 LLM API、不调用 QMT 交易接口、不调用 `xttrader`、不真实发送通知、不下单。

## 下一阶段计划

阶段二十九通过后的下一阶段是阶段三十：小资金实盘灰度准备。阶段三十仍默认关闭实盘，不允许自动下单，不允许绕过 Human Approval / Risk Gate / Live Readiness Audit。
