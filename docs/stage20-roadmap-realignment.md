# 阶段二十：项目路线总文档重审与阶段计划对齐

## 为什么要做阶段二十

阶段一到阶段十九已经完成了安全边界、QMT Gateway、Risk Gate、ETF Rotation、DataHub、Research、Model Lab、Backtest / Shadow Replay、Daily Pipeline、Reporting、Scheduler、本地历史行情缓存、QMT historical provider、cache warmup、ETF universe warmup、cached research、cached ETF rotation 以及 pipeline data source decision。

随着阶段推进，`docs/qmt-ai-trading-project-roadmap.md` 中部分阶段名称仍停留在宏观表达，和实际工程拆分粒度出现偏差。阶段二十的目标是重新审视完整路线，重写总路线文档，固化后续阶段提示词和开发规则，防止后续开发越级接实盘或绕过安全边界。

## 阶段十九与原 roadmap 表达不一致的原因

原 roadmap 中“阶段十九：Daily Pipeline 接入真实缓存行情”是宏观目标，实际阶段十九完成的是“Daily Pipeline 数据源切换策略”。两者方向接近，但表述粒度不同：

- 宏观目标强调 Daily Pipeline 未来应使用真实缓存行情。
- 实际工程实现先建立数据源决策层，明确 `legacy`、`cached`、`auto`、`mock` 的选择逻辑。
- 实际工程实现先记录 cache coverage、confidence、fallback warning，避免 mock/fallback 被误认为真实行情。
- 在真实缓存数据质量长期验证前，不应直接把真实缓存行情默认化。

## 结论

阶段十九不是完全跑偏，而是工程拆分粒度不一致。它是“Daily Pipeline 接入真实缓存行情”的安全前置和工程化表达。真正的“Daily Pipeline 真实缓存数据默认化”应放在后续数据质量验证通过之后执行。

## 本阶段如何修正 roadmap

阶段二十将 `docs/qmt-ai-trading-project-roadmap.md` 重写为完整项目总路线文档，补充：

- 后续开发强制阅读规则。
- 项目定位、最初需求与目标回顾。
- 当前总体架构和安全边界。
- 阶段一到阶段十九完整完成情况。
- 当前系统能力与仍缺失能力。
- 阶段二十到阶段三十一的修正后计划。
- 阶段命名与实际任务对齐规则。
- 后续 Codex 提示词模板规则。

## 后续阶段如何防止跑偏

后续每个阶段开始前必须先读 roadmap，再读架构文档，再读最近一个已完成阶段文档。每个阶段提示词必须明确已完成阶段、本阶段目标、本阶段验收标准、本阶段通过后的下一阶段计划。如果阶段目标和 roadmap 不一致，必须先更新 roadmap 或说明原因。

后续小修复优先用本地脚本修，不大改架构；不越级接实盘；不为了测试绕过风控；不整体引入 Qlib / vn.py / TradingAgents 源码。

## 当前阶段安全约束

阶段二十只做路线文档、计划对齐、文档测试、开发规则固化：

- 当前不做交易功能。
- 当前不调用 QMT。
- 当前不调用 `xttrader`。
- 当前不下单。
- 当前不查询资金、持仓、订单、成交。
- 当前不真实发送通知。
- 当前不修改 `scripts/sync_all.ps1`。

## 阶段二十通过后的下一阶段计划

阶段二十一：Human Approval 人工确认层。

目标是在 TradeIntent 生成后加入人工审批对象、本地审批文件和 CLI 审批流程。默认只生成 pending approval；未批准不得进入 paper/live 执行链路。阶段二十一仍不实盘、不调用 `xttrader`、不真实下单。
