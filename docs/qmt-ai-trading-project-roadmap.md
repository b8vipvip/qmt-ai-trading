# qmt-ai-trading 项目总路线与阶段计划

## 0. 后续开发强制阅读规则

- 每个新阶段开始前，必须先阅读 `docs/qmt-ai-trading-project-roadmap.md`。
- 再阅读 `docs/qmt-ai-trading-architecture.md`。
- 再阅读最近一个已完成阶段文档。
- 再确认当前阶段是否符合本文档路线。
- 如果阶段目标与本文档不一致，必须优先更新路线文档或说明原因。
- 每个阶段开发提示词必须写明：已完成阶段、本阶段目标、本阶段验收标准、本阶段通过后的下一阶段计划。
- 每个阶段开发提示词必须写明当前阶段通过后的下一阶段计划。
- 小修复优先本地脚本修，不要大改架构。
- 不要越级接实盘。
- 不要为了测试绕过风控。

## 1. 项目定位

qmt-ai-trading 是个人本地 A股 / ETF / QMT / AI Agent 辅助量化系统。当前默认运行模式是 dry-run / shadow，当前仍未开启实盘。项目优先级是安全边界与风控优先，而不是尽快下单。

核心定位如下：

- AI 不直接下单。
- Research / Model Lab / Agent 只生成评分、解释、建议或 TradeIntent。
- QMT Gateway 是唯一真实交易边界。
- 所有交易必须经过 Risk Gate。
- QMT Gateway 只执行已经通过审批和风控的结构化指令，不做策略判断。
- 实盘前必须具备 Human Approval、Paper Trading、实盘前安全审计、小资金灰度。

## 2. 最初需求与目标回顾

项目最初目标不是简单写一个策略脚本，而是构建完整的本地 QMT AI 辅助量化系统。路线选择是先搭安全边界，再搭数据，再搭研究，再搭策略，再搭 pipeline，再搭调度，再逐步接近实盘。

项目借鉴外部优秀工程思想，但不整体引入外部项目源码：

- 借鉴 Qlib 的数据、研究、模型实验和因子评估思想。
- 借鉴 vn.py / VeighNa 的数据管理、回测、交易工程和网关边界思想。
- 借鉴 TradingAgents 的多 Agent 分析、解释和研究协作思想。
- 不整体引入 Qlib / vn.py / TradingAgents 源码，避免工程复杂度失控。

策略路线优先 ETF 轮动，后续再扩展多因子选股、多策略组合、Agent Research。

## 3. 当前总体架构

```text
ETF Universe
-> Universe Warmup
-> LocalBarStore / market_data
-> Pipeline Data Source Decision
-> Cached Research
-> Cached ETF Rotation
-> TradeIntent
-> Risk Gate
-> Backtest / Shadow Replay
-> Reporting
-> Scheduler
-> Human Approval
-> Paper Trading / QMT dry-run
-> Future Live Trading
```

职责边界：

- ETF Universe：维护可研究、可交易、可缓存的 ETF 标的池。
- Universe Warmup：根据 ETF Universe 自动补齐本地历史行情缓存；默认 mock，可选 QMT historical provider；不交易。
- LocalBarStore / market_data：本地历史行情缓存层；`market_data/` 是本地运行数据，不提交 Git。
- Pipeline Data Source Decision：Daily Pipeline 的数据源决策层，判断 legacy / cached / auto / mock、cache coverage、confidence 和 fallback warning。
- Cached Research：只读本地缓存行情，生成 research factors、scores、warnings 和 candidates；不下载数据、不下单。
- Cached ETF Rotation：将缓存研究评分转为 ETF Rotation 候选、排序、权重和 dry-run TradeIntent。
- TradeIntent：策略层输出的结构化交易意图，不等同于订单。
- Risk Gate：所有 TradeIntent 进入执行边界前必须通过的风控闸门。
- Backtest / Shadow Replay：模拟历史或影子执行过程，用于验证信号、风险和报告，不触达实盘。
- Reporting：输出 Markdown / JSON / HTML 报告，记录数据源、信号、风控和 dry-run 结果。
- Scheduler：本地 Windows 调度封装，默认 dry-run / preview，不越级执行实盘。
- Human Approval：阶段二十一人工确认层；TradeIntent / Risk Gate 之后生成本地 pending approval，未批准不得进入 paper/live 执行链路。
- Future Paper Trading：未来 paper / QMT dry-run 订单生命周期模拟。
- Future Live Trading：未来小资金灰度实盘；默认关闭，必须多重确认。

## 4. 当前安全边界

- 不提交 `.env` / token / key / 数据库 / `market_data/` / `reports/` / `logs/`。
- 不修改 `scripts/sync_all.ps1`。
- 不调用 `xttrader`。
- 不真实下单。
- 不查资金、持仓、订单、成交。
- 不真实发送通知。
- fallback/mock 数据只能用于 dry-run validation，不能作为实盘交易依据。
- AI / Research / Model Lab / Agent 不能绕过 Risk Gate。
- QMT Gateway 不做策略判断，只执行已批准指令。
- Live Trading 默认关闭。

## 5. 已完成阶段总览

| 阶段 | 阶段名称 | 阶段目标 | 核心模块 | 当前状态 | 验收重点 |
| --- | --- | --- | --- | --- | --- |
| 一 | 项目安全和结构基线 | 建立项目结构、敏感信息保护和基础安全规则 | 目录结构、`.gitignore`、配置模板 | 已完成 | 敏感文件和运行产物不提交 |
| 二 | QMT Gateway 标准化 | 明确 QMT Gateway 为唯一交易边界 | Gateway models、order safety | 已完成 | 交易接口集中封装，默认安全 |
| 三 | Risk Gate 完整化 | 建立 TradeIntent 风控校验 | Risk rules、RiskDecision | 已完成 | TradeIntent 必须先过 Risk Gate |
| 四 | ETF 轮动 Strategy Engine 标准化 | 标准化 ETF rotation 候选、评分、信号 | ETF rotation、scoring | 已完成 | 策略输出结构化信号/TradeIntent |
| 五 | Data Hub 标准化 | 统一数据入口和 MarketBar 模型 | DataHub providers、models | 已完成 | 数据层不直接下单，接口统一 |
| 六 | Research 层标准化 | 建立研究因子、评分和候选输出 | Research factors、scoring | 已完成 | Research 与交易执行解耦 |
| 七 | Research Model Lab | 建立轻量模型实验与评估 | dataset、metrics、model_lab | 已完成 | 模型实验只输出预测/评价 |
| 八 | Backtest / Shadow Replay 标准化 | 建立回测和影子复盘基线 | Backtest、Shadow Replay | 已完成 | 模拟执行不触达真实交易 |
| 九 | Signal Pipeline / Daily Runner 标准化 | 串联数据、策略、风控、报告的每日流程 | Daily Pipeline、runner | 已完成 | dry-run pipeline 可执行 |
| 十 | Report / Notification 输出层标准化 | 输出 Markdown / JSON / HTML 报告和通知占位 | Reporting、notifier dry-run | 已完成 | 通知默认 dry-run，不发真实消息 |
| 十一 | Windows Scheduler 本地调度标准化 | 封装本地计划任务预览和 dry-run 调度 | scheduler、scheduled runner | 已完成 | 不传 execute 只预览，不修改系统任务 |
| 十二 | Historical Data Cache / Local Market Data Store | 建立本地历史行情缓存 | LocalBarStore、BarQuery | 已完成 | cache hit/miss/warmup 可验证 |
| 十三 | QMT Historical Provider Adapter | 可选接入 QMT historical provider | QmtHistoricalDataProvider | 已完成 | 只导入 xtdata，不调用 xttrader |
| 十四 | QMT Historical Provider 实机联调 + 数据字段校准 | 支持字段校准和样本诊断 | diagnostics、field mapping | 已完成 | 小范围样本拉取与字段报告 |
| 十五 | QMT 历史数据自动补全接入 Scheduler | scheduler 前置 cache warmup | cache_warmup、scheduled pipeline | 已完成 | warmup 支持 mock/qmt，失败安全 |
| 十六 | ETF Universe 历史数据自动补全策略 + 项目总路线文档 | ETF universe 批量 warmup，并形成路线文档 | universe warmup、roadmap | 已完成 | 标的池缓存补全，不交易 |
| 十七 | Research 使用缓存历史数据 | Research 只读 LocalBarStore 生成评分 | cached research | 已完成 | 缓存不足输出 warning，不下载不交易 |
| 十八 | Cached ETF Rotation：ETF 策略从缓存历史因子生成信号 | 将 cached research 接入 ETF rotation | cached_etf_rotation | 已完成 | 缓存充足时可生成 dry-run TradeIntent |
| 十九 | Daily Pipeline 数据源切换策略 | 为 Daily Pipeline 建立数据源选择和可信度判断 | pipeline data_source | 已完成 | selected_source、coverage、confidence、fallback warning 清晰 |
| 二十 | 项目路线总文档重审与阶段计划对齐 | 重审路线并对齐阶段计划 | roadmap、stage20 docs | 已完成 | 阶段编号无冲突，后续提示词规则清晰 |
| 二十一 | Human Approval 人工确认层 | 在 TradeIntent/Risk Gate 后加入人工审批文件和 CLI | approval、approval_cli | 已完成 | 默认 pending，未批准阻断 paper/live，不调用 QMT/xttrader |
| 二十二 | Paper Trading / QMT dry-run 适配 | 在 Human Approval 后加入本地 paper order 生命周期模拟 | paper、paper_trading_cli | 已完成 | 只读取 APPROVED approval，确认 RiskDecision allowed=True，不调用 QMT/xttrader |

阶段十九：Daily Pipeline 数据源切换策略。这是“Daily Pipeline 接入真实缓存行情”的安全前置和实际工程化表达。它通过 `data_source_mode=legacy/cached/auto/mock`、cache coverage、confidence、fallback warning，确保 pipeline 知道自己使用的是什么数据源，避免把 mock/fallback 当成真实行情。

## 6. 当前系统能力清单

当前已经具备：

- 项目结构和敏感信息保护
- TradeIntent / RiskDecision / OrderResult 等核心模型
- QMT Gateway 安全边界
- Risk Gate
- ETF Rotation
- DataHub
- Research factors / scoring
- Model Lab
- Backtest / Shadow Replay
- Daily Pipeline
- Markdown / JSON / HTML reporting
- Notification dry-run
- Windows Scheduler dry-run
- LocalBarStore 历史行情缓存
- QMT historical provider 可选接入
- QMT diagnostics / field calibration
- cache warmup
- ETF universe warmup
- cached research
- cached ETF rotation
- pipeline data source decision
- Human Approval 本地审批对象、审批文件、CLI 审批和审批状态检查
- Paper Trading 本地订单生命周期模拟、paper order/report 文件、CLI 查看/取消

## 7. 当前仍缺失的关键能力

当前仍缺失：

- 实盘前安全审计
- QMT xtquant 实机环境校准与真实样本数据验证
- 真实数据长期缓存质量检查
- 真实回测/归因/绩效评估
- 资金管理与组合层
- 多策略组合
- Agent Research Layer
- 异常监控、告警、熔断
- 小资金灰度实盘流程
- UI / Dashboard 后置

## 8. 修正后的后续阶段计划

### 阶段二十：项目路线总文档重审与阶段计划对齐

- 本阶段，即当前阶段。
- 重写 roadmap，固化后续开发规则。
- 不开发交易功能。

### 阶段二十一：Human Approval 人工确认层

- 在 TradeIntent 生成并通过 Risk Gate 后加入人工确认对象和本地审批文件。
- 新增 `qmt_ai_trading.approval`、`scripts/approval_cli.py` 和 pipeline `--create-approval`。
- 默认只生成 pending approval，不自动 approve。
- 未批准不得进入 paper/live 执行链路。
- Approval 不等于下单，不调用 QMT，不调用 `xttrader`。
- 当前状态：已完成。

### 阶段二十二：Paper Trading / QMT dry-run 适配

- 在 Human Approval 之后、Live Trading 之前，模拟本地 paper order 生命周期。
- 只读取 `APPROVED` approval request，确认 `trade_intents` 非空且 `risk_decisions allowed=True`。
- 记录 paper order、submitted/filled/cancelled/rejected 状态和 paper execution report。
- 当前状态：已完成。仍不调用 QMT、不调用 `xttrader`、不真实下单。

### 阶段二十三：实盘前安全审计

- 检查 live trading 开关、Risk Gate、Human Approval、日志、配置、黑名单、仓位限制、敏感信息。
- 生成 go/no-go 报告。

### 阶段二十四：QMT 实机数据联调与真实缓存质量验证

- 在真实 MiniQMT / xtquant 环境中拉取小范围 ETF 历史数据。
- 校验字段、日期、复权、成交量、缺失值、重复值。
- 不交易。

### 阶段二十五：Daily Pipeline 真实缓存数据默认化

- 在数据质量达标后，让 cached 模式成为默认 dry-run 数据源。
- mock fallback 必须显式开启。
- 报告中写出数据可信度。

### 阶段二十六：组合与资金管理层

- 多 ETF 权重、最大仓位、现金保留、调仓阈值。
- 仍 dry-run / paper。

### 阶段二十七：长期回测与绩效归因

- 多周期回测、收益/回撤/换手/胜率/因子贡献。
- 形成稳定评估报告。

### 阶段二十八：异常监控、告警、熔断

- 数据缺失、缓存异常、信号异常、风险异常、任务失败时告警。
- 默认通知 dry-run，可后续接真实通知。

### 阶段二十九：Agent Research Layer

- Agent 只做解释、研究摘要、风险提示、对比分析。
- Agent 不得下单。
- Agent 不得绕过 Risk Gate。

### 阶段三十：小资金实盘灰度准备

- 仅在前面全部通过后。
- 默认仍关闭。
- 必须 Human Approval + Risk Gate + live config 三重确认。
- 小资金、白名单标的、严格日志。

### 阶段三十一：UI / Dashboard

- 后端稳定后再做。
- 展示报告、审批、风险、缓存覆盖率、任务状态。
- 不把 UI 作为交易绕过入口。

## 9. 阶段命名与实际任务对齐规则

- 如果 roadmap 阶段名是宏观目标，实际开发可以拆成安全前置子阶段，但必须更新 roadmap 说明。
- 例如原“Daily Pipeline 接入真实缓存行情”已经拆解为：
  1. Cached Research
  2. Cached ETF Rotation
  3. Pipeline Data Source Decision
  4. 后续再做真实缓存数据默认化
- 不允许出现“提示词阶段目标”和 roadmap 完全不一致且未说明原因的情况。

## 10. 后续 Codex 开发规则与提示词模板规则

每次 Codex 提示词必须包含：

- 当前必须先阅读的 docs 列表
- 已完成阶段列表
- 当前阶段目标
- 当前阶段设计原则
- 具体任务
- 测试清单
- 禁止事项
- 最后输出要求
- 当前阶段通过后的下一阶段计划

## 阶段二十三补充：实盘前安全审计

阶段二十三是“实盘前安全审计”。本阶段在 Paper Trading / QMT dry-run 之后建立 Live Readiness Audit 框架，用于检查 roadmap / architecture 一致性、Risk Gate、Human Approval、Paper Trading、QMT Gateway、安全配置、运行产物忽略规则、敏感模式、禁止 `xttrader` import、禁止绕过 Risk Gate 的直接下单调用，并生成结构化 go/no-go 审计报告。

阶段二十三完成状态：已建立审计模型、静态检查、审计服务、Markdown/JSON formatter、CLI、测试和阶段文档。当前阶段默认 `NO_GO`，`allow_go=False`，审计报告不是交易授权；本阶段不调用 QMT、不调用 `xttrader`、不真实下单、不查询资金/持仓/订单/成交。

阶段二十四确认：阶段二十四是“QMT 实机数据联调与真实缓存质量验证”。目标是在真实 MiniQMT / xtquant 环境中小范围拉取 ETF 历史数据，校验字段、日期、复权、成交量、缺失值、重复值和缓存质量。阶段二十四仍不实盘、不调用 `xttrader`、不真实下单。

后续开发前必须继续先读 `docs/qmt-ai-trading-project-roadmap.md`，再读 `docs/qmt-ai-trading-architecture.md`，再读最近一个已完成阶段文档；不得越级接实盘，不得为了测试绕过风控。

## 阶段二十四：QMT 实机数据联调与真实缓存质量验证

阶段二十四确认名称为“QMT 实机数据联调与真实缓存质量验证”。本阶段目标是在真实 MiniQMT / `xtquant.xtdata` 环境可用时，小范围拉取 ETF 历史 K 线样本，保存到 `market_data_qmt_stage24/`，再从 `LocalBarStore` 读取验证 cache hit，并生成 Markdown / JSON 数据质量报告。

阶段二十四完成状态说明：

- 新增 `qmt_ai_trading.datahub.qmt_quality`，提供 `QmtDataQualityReport`、质量检查、cache roundtrip 和 Markdown / JSON 格式化。
- 新增 `qmt_ai_trading.datahub.qmt_realdata_plan`，默认限制 `max_symbols=5`、`max_days=90`，防止误拉大规模真实行情。
- 扩展 QMT runtime diagnostics，输出 `xtdata` 可用性、行情函数支持情况、连接状态和默认不导入交易接口的风险说明。
- 新增 `scripts/qmt_realdata_smoke_test.py` 和 `scripts/check_qmt_cache_quality.py`；前者只使用 `xtdata` 行情模块，后者只读本地缓存。
- 无 `xtquant` 环境下默认输出 `UNAVAILABLE` / `SKIPPED` 并生成报告，不导致项目测试崩溃。
- 当前阶段仍不实盘、不调用 `xttrader`、不查询资金/持仓/订单/成交、不下单。

## 阶段二十五：Daily Pipeline 真实缓存数据默认化

阶段二十五确认名称为“Daily Pipeline 真实缓存数据默认化”。阶段二十五将在阶段二十四真实缓存质量验证通过后，把 Daily Pipeline 的默认数据源从 legacy/mock 逐步切换为 cached_real_data 优先；mock fallback 必须显式开启，并在报告中展示真实缓存覆盖率、数据质量等级和信号可信度。阶段二十五仍不实盘、不调用 `xttrader`、不真实下单。

后续开发仍必须先阅读本 roadmap，再阅读 architecture 和最近阶段文档，确认阶段目标与路线一致后再开始开发。

## 阶段二十五：Daily Pipeline 真实缓存数据默认化（已完成）

阶段二十五将 Daily Pipeline 默认数据源切换为 `cached_real_first`：先读取本地 `LocalBarStore` 缓存，再读取阶段二十四生成的 `qmt_data_quality_reports/*.qmt_quality.json` 质量证据，最后由 Cache Quality Gate 决定是否允许生成 dry-run TradeIntent。

完成状态：已新增 `cache_quality_gate`，报告展示 selected_source、cache_root、cache coverage、quality decision、quality report path、confidence、fallback_used、allow_trade_intents 与 remediation。缺少 quality report 时仅允许 dry-run 且 `quality=UNKNOWN`；mock fallback 必须显式开启，不允许静默 fallback。阶段二十五仍不调用 `xttrader`、不调用 QMT 下单、不查询资金/持仓/订单/成交、不实盘。

## 阶段二十六：组合与资金管理层（下一阶段）

阶段二十六目标是在当前单一 ETF top_n 信号基础上，增加组合级权重、最大仓位、现金保留、调仓阈值、持仓计划和组合风险约束。阶段二十六仍 dry-run / paper，不调用 `xttrader`、不真实下单。

## 阶段二十六：组合与资金管理层（已完成）

阶段二十六确认路线为“组合与资金管理层”。本阶段在 Cached ETF Rotation / Strategy 之后、TradeIntent / Risk Gate 之前增加 Portfolio 层，支持 `equal_weight`、`score_weight`、`risk_adjusted_weight`、最大单标的仓位、组合最大仓位、现金保留比例、最小调仓阈值、本地 mock/snapshot 当前持仓输入、`PortfolioPlan` 输出和 dry-run TradeIntent 调整计划。

完成状态：已新增 `qmt_ai_trading/portfolio/`，扩展 Daily Pipeline、pipeline report、scheduled pipeline 与 task registration 参数，并新增 `scripts/run_portfolio_plan.py`。Portfolio plan is dry-run/paper only and is not an order instruction. 阶段二十六不查询真实账户、不调用 QMT 交易接口、不调用 `xttrader`、不真实下单；所有 Portfolio 生成的 TradeIntent 仍必须经过 Risk Gate，进入 paper/live 前仍必须 Human Approval。

## 阶段二十七：长期回测与绩效归因（下一阶段）

阶段二十七确认为“长期回测与绩效归因”。目标是对 `cached_real_first + portfolio plan` 的 dry-run 策略进行多周期回测，输出收益、回撤、换手、胜率、调仓次数、因子贡献和组合归因报告。阶段二十七仍不实盘、不调用 `xttrader`、不真实下单。

后续开发仍必须先阅读本 roadmap，再阅读 architecture 和最近阶段文档，不能越级接实盘，不能为了测试绕过风控。

## 阶段二十七完成状态：长期回测与绩效归因

阶段二十七确认为“长期回测与绩效归因”。本阶段新增 `qmt_ai_trading.performance` 与 `qmt_ai_trading.backtest.long_portfolio_backtest`，用于对 cached_real_first + cached ETF rotation + portfolio plan 的 dry-run 策略做多周期本地缓存回测，输出收益、最大回撤、波动率、Sharpe、胜率、换手、调仓次数、因子贡献、标的归因和 Risk Gate 拦截归因。

阶段二十七只读取 `LocalBarStore` 本地缓存，不调用 QMT 交易接口，不调用 `xttrader`，不真实下单，不查询真实资金、持仓、订单或成交。Risk Gate 拒绝的模拟 TradeIntent 会单独记录，不计入 risk-executable performance。

阶段二十八确认为“异常监控、告警、熔断”。阶段二十八将在长期回测之后，对数据缺失、缓存异常、信号异常、Risk Gate 连续拒绝、回测异常和调度失败建立监控事件、告警等级和熔断规则。后续开发前仍必须先读本 roadmap、architecture 和最近阶段文档。


## 阶段二十八完成状态：异常监控、告警、熔断

阶段二十八确认为“异常监控、告警、熔断”（已完成）。本阶段新增 `qmt_ai_trading.monitoring` 与 `scripts/run_monitoring_check.py`，用于对数据质量、fallback/mock 使用、Risk Gate 拒绝数量、调度退出码和最大回撤做本地 dry-run 监控，输出 Markdown / JSON 报告、本地 dry-run alert 文件和 circuit-breaker 建议。

阶段二十八不发送真实通知、不调用 QMT 交易接口、不调用 `xttrader`、不真实下单、不查询真实资金、持仓、订单或成交。Circuit breaker 是阻断建议和人工复核信号，不是自动实盘控制。阶段二十九确认为“Agent Research Layer”，Agent 仍只能做研究解释和风险提示，不能下单，不能绕过 Risk Gate。


## 阶段二十九：Agent Research Layer（下一阶段）

阶段二十九确认为“Agent Research Layer”。下一阶段只允许在 Research / Reporting / Monitoring 产物之上做研究解释、因子归因摘要、异常原因分析和风险提示；Agent 不得下单，不得调用 `xttrader`，不得查询真实资金、持仓、订单或成交，不得绕过 Risk Gate、Human Approval、Paper Trading、Live Readiness Audit 或阶段二十八 Circuit Breaker。

后续任何开发前必须先读本 roadmap，再读 architecture 和最近阶段文档；不能越级接实盘，不能为了测试绕过风控，不能把 dry-run alert 或 circuit-breaker 建议解释为交易授权。

## 阶段二十九：Agent Research Layer（已完成）

阶段二十九新增只读 Agent Research Layer。该层位于 Daily Pipeline、Monitoring、Long Backtest、Portfolio 和 Risk Gate 输出之后，用于汇总 Daily Pipeline 报告、Monitoring Report、Long Backtest Result、Portfolio Plan、RiskDecision 和 Cache Quality 信息，生成结构化 Research Memo、Signal Explanation、Risk Summary、Backtest Summary、Monitoring Summary、Candidate Comparison 和 Human Review Checklist。

阶段二十九默认使用 deterministic `local_rules` summarizer；`external_llm_disabled` 模式只输出禁用说明。当前阶段不调用外部 LLM API，不读取真实 key，不调用 QMT 交易接口，不调用 `xttrader`，不真实发送通知，不下单，不绕过 Risk Gate / Human Approval。

后续开发前仍必须先读本 roadmap、architecture 和最近阶段文档。

## 阶段三十：小资金实盘灰度准备（下一阶段）

阶段三十目标是在 dry-run / paper / monitoring / agent research 能力通过后，建立极小资金灰度实盘准备清单、live config 审计、白名单标的、人工审批流程和多重开关验证。阶段三十仍默认关闭实盘，不允许自动下单，不允许绕过 Human Approval / Risk Gate / Live Readiness Audit。

## 阶段三十：小资金实盘灰度准备（已完成）

阶段三十新增 Live Gray Readiness 准备层，位于 Risk Gate / Human Approval / Paper Trading / Live Readiness Audit / Monitoring / Agent Research 之后。该阶段只生成小资金灰度准备配置、只读检查、人工复核 checklist、Markdown / JSON readiness report；默认 `live_enabled=False`、`gray_enabled=False`、默认 `NO_GO`，不调用 QMT 交易接口、不调用 `xttrader`、不真实发送通知、不下单。

阶段三十完成状态：已建立 `qmt_ai_trading/liveprep/`、`scripts/run_live_gray_readiness.py`、Daily Pipeline 可选 Live Gray Readiness 区块、scheduled/register 参数透传和阶段三十文档。后续开发前仍必须先读 roadmap 与 architecture，不得越级接实盘，不得绕过风控。

## 阶段三十一：UI / Dashboard（下一阶段）

阶段三十一计划建立本地只读 dashboard，用于展示报告、审批状态、风险状态、缓存覆盖率、监控事件、Agent Research Memo 和 Live Gray Readiness。UI 不得作为交易绕过入口，不得直接触发实盘，不得绕过 Risk Gate / Human Approval。

## 阶段三十一：UI / Dashboard（已完成）

阶段三十一确认阶段名称为“UI / Dashboard”。本阶段新增本地只读静态 Dashboard，位于 Reporting / Monitoring / Agent Research / Live Gray Readiness 之后，用于汇总 Daily Pipeline、Cache Quality、Candidates、TradeIntents、RiskDecision、Portfolio Plan、Monitoring、Agent Research、Live Gray Readiness、Human Approval 和 Paper Trading 本地报告或状态文件。

Dashboard 只生成单文件 HTML；`scripts/build_dashboard.py` 可从本地报告目录生成页面，`scripts/run_dashboard_preview.py` 可打印本地路径或启动 Python 标准库只读静态服务，`run_daily_pipeline.py --build-dashboard` 可在 pipeline 完成后生成页面。Dashboard 不提供下单按钮，不触发 Approval / Paper / Live，不调用 QMT 交易接口，不调用 `xttrader`，不真实发送通知，不下单，不读取 `.env`、token、key、password、secret。

后续开发前仍必须先读 roadmap、architecture 和最近阶段文档，不得越级接实盘，不得为了测试绕过 Risk Gate 或 Human Approval。

## 阶段三十二：运行手册 / 部署手册 / 总体验收（下一阶段）

阶段三十二确认阶段名称为“运行手册 / 部署手册 / 总体验收”。目标是把当前系统的本地运行、数据缓存、Daily Pipeline、Scheduler、Approval、Paper、Monitoring、Agent、Live Gray、Dashboard 全链路整理成操作手册和总体验收清单。阶段三十二仍不实盘、不调用 `xttrader`、不真实下单。
