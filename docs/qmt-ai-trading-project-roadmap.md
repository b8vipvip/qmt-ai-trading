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

## 阶段三十二：运行手册 / 部署手册 / 总体验收

阶段三十二确认名称为“运行手册 / 部署手册 / 总体验收”。本阶段目标是把本地运行、数据缓存、Daily Pipeline、Scheduler、Approval、Paper Trading、Monitoring、Agent Research、Live Gray Readiness、Dashboard 全链路整理为操作手册、部署手册、故障排查入口和总体验收清单，并新增只读 Final Acceptance 与 Full Dry Run Smoke。

阶段三十二完成状态说明：已新增 runbook 文档、final acceptance 检查包、dry-run smoke 脚本和阶段三十二验收测试。该阶段仍不实盘、不调用 QMT 交易接口、不调用 `xttrader`、不查询真实资金/持仓/订单/成交、不真实发送通知、不下单。

项目总体验收完成 / 后续增强待定。后续开发前必须先读 roadmap，任何新增强必须在新的人工确认阶段中明确授权，默认 dry-run，不能绕过 Risk Gate / Human Approval / Live Readiness Audit。

## 阶段三十三：真实 QMT 数据质量长期追踪（已完成）

阶段三十三确认路线为“真实 QMT 数据质量长期追踪”。目标是把多日 QMT historical cache quality report 与 LocalBarStore 只读缓存扫描汇总为长期 Data Quality Ledger、Trend Report、Incident Report 和 DataQualityTrackingReport，并接入 Monitoring / Dashboard / Daily Pipeline 的只读视图。

阶段三十三完成状态：已新增 `qmt_ai_trading.data_quality` 包、CLI、Monitoring 规则、Dashboard section、Daily Pipeline 可选参数、scheduled/register 参数与阶段测试。当前阶段不调用 QMT 交易接口、不调用 xttrader、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单。后续开发前必须继续先读 roadmap。

## 阶段三十四：真实通知 dry-run 接入准备（下一阶段）

阶段三十四确认路线为“真实通知 dry-run 接入准备”。目标是为邮件、Telegram、企业微信等真实通知通道建立 dry-run 配置验证、消息模板、敏感信息保护和发送前审计；默认不真实发送通知、不读取真实 token、不调用外部网络。

## 阶段三十四：真实通知 dry-run 接入准备（已完成）

阶段三十四确认路线为“真实通知 dry-run 接入准备”。本阶段新增统一 Notification Dry Run 层，支持 `NotificationMessage`、`NotificationRecipient`、`NotificationDeliveryPlan`、`NotificationAuditResult`、`NotificationDryRunReport`，支持 FILE / CONSOLE 本地预览，并为 EMAIL / TELEGRAM / WECHAT 生成 dry-run / suppressed delivery plan。

阶段三十四完成状态：已新增 `qmt_ai_trading.notification_dryrun` 包、`scripts/run_notification_dry_run.py`、Daily Pipeline 可选 `--enable-notification-dry-run`、scheduled/register 参数透传、Dashboard Notification Dry Run section、阶段文档与测试。当前阶段不读取真实 token/key/password/secret，不调用 SMTP / Telegram API / 企业微信 API，不调用外部网络，不真实发送通知；不调用 QMT 交易接口、不调用 xttrader、不下单。后续开发前必须继续先读 roadmap。

## 阶段三十五：小资金灰度人工流程演练（下一阶段）

阶段三十五确认为“小资金灰度人工流程演练”。目标是在不启用真实实盘的前提下，演练从信号生成、Risk Gate、Human Approval、Paper Trading、Monitoring、Agent Research、Live Gray Readiness、Notification Dry Run 到 Dashboard 的完整人工流程。阶段三十五仍默认 dry-run，不真实下单，不调用 xttrader，不真实发送通知。

## 阶段三十五：小资金灰度人工流程演练（已完成）

阶段三十五确认当前路线为“小资金灰度人工流程演练”。本阶段新增 Gray Rehearsal，本地 dry-run 串联 Pipeline / Monitoring / Data Quality Tracking / Agent Research / Live Gray Readiness / Notification Dry Run / Dashboard 之后的人工复核链路，生成演练计划、场景配置、步骤台账、人工 Checklist 与 Markdown/JSON 结果报告。

完成状态：支持 `scripts/run_gray_rehearsal.py` 独立运行；支持 `run_daily_pipeline.py --enable-gray-rehearsal` 可选输出 Gray Rehearsal 区块；支持 scheduled pipeline 与 register task 透传 gray rehearsal 参数；Dashboard 支持只读 Gray Rehearsal section。阶段三十五不启用实盘、不调用 QMT 交易接口、不调用 `xttrader`、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单。

## 阶段三十六：小资金灰度准入复核 / 人工决策包（下一阶段）

阶段三十六目标是在不启用真实实盘的前提下，把阶段三十五演练结果整理成一份人工决策包，用于人工判断是否有资格在未来单独阶段进入极小资金灰度。阶段三十六仍默认 dry-run，不真实下单，不调用 `xttrader`，不真实发送通知。

后续开发前必须继续先读 roadmap，再读 architecture，再读最近阶段文档。

## 阶段三十六：小资金灰度准入复核 / 人工决策包（已完成）

阶段三十六确认阶段名称为“小资金灰度准入复核 / 人工决策包”。本阶段新增 `qmt_ai_trading.gray_decision` manual-only 决策包层，汇总 Risk Gate、Human Approval、Paper Trading、Live Readiness Audit、Monitoring、Data Quality Tracking、Agent Research、Live Gray Readiness、Notification Dry Run、Dashboard、Gray Rehearsal 和 Final Acceptance 本地证据，输出 Markdown / JSON 人工决策包、Checklist、人工签字占位和 NOT_ELIGIBLE / NEED_MORE_EVIDENCE / READY_FOR_MANUAL_DECISION / BLOCKED 结论。

完成状态：支持 `scripts/run_gray_decision_package.py` 独立运行；支持 `run_daily_pipeline.py --enable-gray-decision-package` 可选输出 Gray Decision Package 区块；支持 scheduled pipeline 与 register task 透传 gray decision package 参数；Dashboard 支持只读 Gray Decision Package section。阶段三十六不启用实盘、不调用 QMT 交易接口、不调用 `xttrader`、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单。

## 阶段三十七：极小资金灰度实盘人工审批准备（仍默认关闭）（下一阶段）

阶段三十七确认路线为“极小资金灰度实盘人工审批准备（仍默认关闭）”。目标是在不启用真实实盘的前提下，准备未来极小资金灰度实盘所需的人工审批材料、开关说明、只读配置检查和最终人工确认流程。阶段三十七仍默认关闭实盘，不真实下单，不调用 `xttrader`，不真实发送通知。

后续开发前必须继续先读 roadmap，再读 architecture，再读最近阶段文档；不得越级接实盘，不得为了测试绕过风控。

## 阶段三十七：极小资金灰度实盘人工审批准备（仍默认关闭）

阶段三十七新增 Live Manual Approval Prep，在 Gray Decision Package 之后生成 preparation-only / dry-run 人工审批准备包。目标是汇总 Gray Decision Package、Live Gray Readiness、Gray Rehearsal、Live Readiness Audit、Risk Gate、Human Approval、Paper Trading、Monitoring、Data Quality Tracking、Agent Research、Notification Dry Run、Dashboard 与 Final Acceptance 证据，并生成极小资金范围、允许标的白名单、单笔金额上限、最大仓位上限、禁止事项、残余风险和人工签字页。

完成状态：已新增 `qmt_ai_trading/live_manual_prep/`、`scripts/run_live_manual_prep.py`、Daily Pipeline 可选输出、Scheduler 参数透传、Dashboard 只读 section 和阶段文档。所有 live 开关仍默认关闭；READY_FOR_SIGNOFF 只代表可以让人工审阅签字，不代表允许实盘；本阶段不调用 QMT 交易接口、不调用 xttrader、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单。

## 阶段三十八：极小资金灰度只读环境核验（仍不下单）

阶段三十八计划在仍不启用真实实盘的前提下，对未来极小资金灰度所需的本地 QMT 环境、配置文件、白名单、开关状态、数据质量、审批材料和只读安全边界做最终核验。阶段三十八仍不真实下单，不调用 xttrader，不真实发送通知。

## 阶段三十八：极小资金灰度只读环境核验（仍不下单）

阶段三十八确认新增 Live Environment Check，只对未来极小资金灰度可能需要的本地 Python 环境、项目目录、核心脚本、`.gitignore` 运行产物忽略规则、`scripts/sync_all.ps1` 保护状态、敏感文件风险、live 相关开关、scheduler/register dry-run 预览命令、极小资金配置、白名单标的、前置证据材料和只读安全边界做核验。

完成状态说明：系统可通过 `scripts/run_live_env_check.py` 独立生成 Markdown / JSON 只读核验报告；Daily Pipeline 可选 `--enable-live-env-check` 在末尾输出 Live Environment Read-only Check Report；Scheduled Pipeline 和 register task 可透传 live env check 参数；Dashboard 可只读展示 Live Environment Readiness section。

安全说明：`READY_FOR_ENV_REVIEW` 只表示环境材料可交人工复核，不代表允许实盘、不代表自动 GO、不代表交易授权。阶段三十八不启用实盘，不调用 QMT 交易接口，不调用 `xttrader`，不查询账户/资金/持仓/订单/成交，不真实发送通知，不下单。

## 阶段三十九：极小资金灰度最终人工授权包（仍不执行）

阶段三十九计划在仍不执行实盘的前提下，把阶段三十八只读环境核验结果和全部前置材料整理为最终人工授权包。阶段三十九仍不下单、不调用 `xttrader`、不真实发送通知、不查询账户资金持仓订单成交。

## 阶段三十九：极小资金灰度最终人工授权包（仍不执行）

阶段三十九新增 Final Authorization Package，用于把阶段三十八 Live Env Check 和前置 Live Manual Prep、Gray Decision Package、Gray Rehearsal、Live Gray Readiness、Live Readiness Audit、Risk Gate、Human Approval、Paper Trading、Monitoring、Data Quality Tracking、Agent Research、Notification Dry Run、Dashboard、Final Acceptance 证据汇总为最终人工审阅材料包。该阶段已完成 review-only Markdown / JSON 输出、CLI、Daily Pipeline 可选区块、Scheduled / register 参数透传和 Dashboard 只读 section。

`READY_FOR_FINAL_SIGNOFF_REVIEW` 只代表材料可以交人工最终签字审阅，不代表允许实盘、不代表交易授权、不代表自动 GO。阶段三十九不启用实盘、不调用 QMT 交易接口、不调用 xttrader、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单。

## 阶段四十：实盘开关隔离与最终红线复核（仍默认关闭）

阶段四十计划在仍不执行实盘的前提下，对所有 live 开关、execute 开关、真实通知开关、QMT/xttrader 边界、账户查询边界和计划任务注册边界做最终红线复核。阶段四十仍默认关闭实盘，不下单、不调用 xttrader、不真实发送通知、不查询账户资金持仓订单成交。

## 阶段四十：实盘开关隔离与最终红线复核（仍默认关闭）

阶段四十已新增 Red-line Review 能力：扫描 live / execute / real-send / xttrader / QMT 交易 API / 账户资金持仓订单成交查询 / scheduler preview / Dashboard order entry / 敏感文件边界，并生成 review-only Markdown / JSON 报告。`READY_FOR_REDLINE_REVIEW` 只代表材料可交人工红线复核，不代表允许实盘。本阶段不启用实盘、不调用 QMT、不调用 xttrader、不真实发送通知、不下单。

## 阶段四十一：极小资金灰度实盘前只读确认台账（仍不执行）

下一阶段计划在仍不执行实盘的前提下，把阶段四十红线复核结果、阶段三十九最终人工授权包、阶段三十八只读环境核验和全部前置证据整理为只读确认台账。阶段四十一仍不下单、不调用 xttrader、不真实发送通知、不查询账户资金持仓订单成交。

后续开发前必须先读 roadmap。小修复优先本地脚本修，不要大改架构。

### 阶段四十一：极小资金灰度实盘前只读确认台账

- 当前状态：已完成。
- 新增 `qmt_ai_trading.live_gray_ledger`，只读汇总 Stage37 / Stage38 / Stage39 / Stage40 本地证据。
- 输出 `live_gray_ledger.md` / `live_gray_ledger.json`，明确 `READY_FOR_MANUAL_REVIEW` 只表示材料可供人工复核，不是实盘授权。
- 本阶段不调用 `xttrader`，不调用 QMT 交易接口，不下单，不查询真实资金/持仓/订单/成交，不发送真实通知。
- Daily Pipeline / Scheduled Pipeline / register preview 仅增加可选 ledger dry-run 参数，默认不开启，不改变默认行为。

### 阶段四十二：灰度前人工复核包与只读演练封版（预告）

- Stage42 仍不是实盘，不真实下单。
- 只在 Stage41 台账基础上生成更严格的人工复核包、只读演练清单和最终 go/no-go 决策材料。
- 仍不能自动 approve，不能调用 `xttrader`，不能查询真实账户，不能真实通知。

## 阶段四十二：灰度前人工复核包与只读演练封版（已完成）

Stage42 在 Stage41 只读台账基础上生成灰度前人工复核包与只读演练封版材料。该阶段不调用 xttrader、不下单、不查询真实账户、不发送真实通知；`READY_FOR_HUMAN_REVIEW` 只表示材料可供人工复核，不代表实盘授权。

### Stage43 预告

阶段四十三建议为“灰度前人工签字清单与配置封存”。Stage43 仍不能直接实盘，只能继续做人工签字、只读演练、配置封存或更严格的灰度前检查。

### 阶段四十三：灰度前人工签字清单与配置封存

- 当前状态：已完成。
- 在 Stage42 人工复核包基础上，生成 Stage43 人工签字清单与配置封存摘要。
- 输出 `live_signature_freeze.md/json` 与 `config_freeze.md/json`，仅作为未来人工会议和配置冻结复核材料。
- `READY_FOR_SIGNATURE` 只表示材料可供人工签字复核，不是实盘授权。
- 本阶段仍不调用 `xttrader`，不下单，不查询资金/持仓/订单/成交，不真实发送通知，不自动 approve，不绕过 Risk Gate 或 Human Approval。

### 阶段四十四预告：灰度前只读环境快照与最终冻结核验

- Stage44 仍不是实盘，不真实下单。
- 只能在 Stage43 人工签字清单与配置封存基础上，生成只读环境快照、配置冻结校验和最终冻结核验摘要。
- Stage44 仍不能自动 approve，不能调用 `xttrader`，不能查询真实账户，不能真实通知。

## Stage44 完成说明与 Stage45 预告

阶段四十四“灰度前配置封存复核与只读环境快照”新增只读环境快照与配置封存复核能力。该阶段只读取本地 Stage40/41/42/43 证据、`.gitignore` 和非敏感配置状态，输出 `live_env_snapshot_stage44/` 运行产物；`READY_FOR_ENV_SNAPSHOT` 仅表示材料可供人工复核，不代表实盘授权。

Stage45 建议名称为“阶段四十五：灰度前只读运行手册与人工流程演练”。Stage45 仍不得直接实盘，只能继续做只读运行手册、人工确认流程演练或更严格的配置冻结复核。

### 阶段四十五：灰度前只读运行手册与人工流程演练

- 当前状态：已完成。
- 在 Stage44 只读环境快照基础上，新增 Stage45 只读运行手册、人工流程演练包和异常处理流程清单。
- `READY_FOR_RUNBOOK_REVIEW` 只表示材料可供人工复核，不代表实盘授权。
- Stage45 不调用 `xttrader`，不真实下单，不查询资金/持仓/订单/成交，不真实发送通知。

### 阶段四十六预告：灰度前运行手册复核与人工演练签字封版

- Stage46 仍不是实盘，不真实下单。
- 只能继续做运行手册复核、人工演练签字、配置冻结复查、异常演练结果和更严格的只读检查。
- 仍不能自动 approve，不能调用 `xttrader`，不能查询真实账户，不能真实通知。

### 阶段四十六：灰度前运行手册复核与人工演练签字封版

- 当前状态：已完成。
- 在 Stage45 只读运行手册与人工流程演练包基础上，新增 Stage46 运行手册复核包、人工演练签字封版材料和异常演练结果摘要。
- Stage46 只读取本地 Markdown / JSON / `.gitignore` 等证据，不调用 `xttrader`，不真实下单，不查询资金/持仓/订单/成交，不真实发送通知。
- `READY_FOR_SIGNOFF_REVIEW` 只表示签字封版材料可供人工复核，不代表实盘授权。

### 阶段四十七：最终只读 go/no-go 材料汇总与人工签字核验

- 下一阶段建议。
- 仍不是实盘，不真实下单，不调用 `xttrader`，不查询真实账户，不真实通知。
- 仅在 Stage46 签字封版材料基础上生成最终只读 go/no-go 材料汇总、人工签字核验清单、缺口列表和下一阶段只读检查计划。

### 阶段四十七：最终只读 go/no-go 材料汇总与人工签字核验

- 当前状态：已完成。
- Stage47 在 Stage46 签字封版材料基础上生成最终只读 go/no-go 材料汇总、人工签字核验清单、缺口列表和下一阶段只读检查计划。
- `READY_FOR_FINAL_REVIEW` / `NEED_MORE_EVIDENCE` / `NO_GO` 只代表材料状态，不代表实盘授权。
- 本阶段不调用 xttrader、不真实下单、不查询真实账户、不真实通知、不注册真实任务。

### 阶段四十八预告：最终只读材料归档与缺口补证计划

- Stage48 仍不是实盘。
- Stage48 只能基于 Stage47 材料继续做最终只读材料归档、缺口补证计划、人工核验结果汇总和下一轮灰度前检查计划。
- Stage48 仍不能自动 approve，不能调用 xttrader，不能查询真实账户，不能真实通知。


### 阶段四十八：最终只读材料归档与缺口补证计划

- 当前状态：已完成。
- 在 Stage47 最终只读 go/no-go 材料基础上，生成 Stage48 最终只读材料归档索引、缺口补证计划、人工核验结果汇总和下一轮灰度前只读检查计划。
- Stage48 仍不是实盘授权，不调用 xttrader，不真实下单，不查询资金/持仓/订单/成交，不真实发送通知。
- `READY_FOR_ARCHIVE_REVIEW` 只表示最终只读归档材料可供人工复核，不代表可以实盘。

### 阶段四十九预告：补证后只读复核与最终材料一致性检查

- Stage49 仍不得直接实盘，只能继续做补证后只读复核、人工核验复查、最终材料一致性检查或更严格的灰度前检查。
- Stage49 仍不能自动 approve，不能调用 xttrader，不能查询真实账户，不能真实通知。

### 阶段四十九：补证后只读复核与最终材料一致性检查

- 当前状态：已完成。
- 在 Stage48 只读归档基础上，新增 `qmt_ai_trading/live_consistency/`，生成补证后只读复核、最终材料一致性检查、人工核验复查和下一轮灰度前检查计划。
- 本阶段仍不是实盘授权，不调用 xttrader，不真实下单，不查询真实账户，不真实通知。
- `READY_FOR_CONSISTENCY_REVIEW` 只表示材料可供人工复核，不代表实盘授权。

### 阶段五十：最终归档复核与材料一致性封版（预告）

- Stage50 仍不得直接实盘。
- 只能继续做最终归档复核、材料一致性封版、人工核验闭环或更严格的灰度前检查。
- 仍不能自动 approve，不能调用 xttrader，不能查询真实账户，不能真实通知。

### 阶段五十：最终归档复核与材料一致性封版

- 当前状态：已完成。
- Stage50 在 Stage49 补证后只读复核与最终材料一致性检查基础上，生成最终归档复核包、材料一致性封版包、人工核验闭环包和下一阶段只读检查计划。
- `READY_FOR_FINAL_ARCHIVE_REVIEW` 只表示最终归档复核与材料一致性封版材料可供人工复核，不代表实盘授权。
- Stage50 不调用 `xttrader`，不调用 QMT 交易接口，不真实下单，不查询资金/持仓/订单/成交，不真实发送通知。
- Stage50 默认 read_only / dry_run_only / no_trade_authorization / no_task_registered。

### 阶段五十一预告：最终只读封版复核与材料归档锁定

- Stage51 仍不得直接实盘。
- Stage51 只能继续做最终只读封版复核、材料归档锁定、人工核验闭环复查或更严格的灰度前检查。
- Stage51 仍不能自动 approve，不能调用 `xttrader`，不能查询真实账户，不能真实通知。

### 阶段五十一：最终只读封版复核与材料归档锁定

- 当前状态：已完成。
- 只读取 Stage47 / Stage48 / Stage49 / Stage50 本地证据与 Stage50 live final archive 输出。
- 生成最终只读封版复核包、材料归档锁定包、人工核验闭环复查包和下一阶段只读检查计划。
- `READY_FOR_LOCK_REVIEW` 只表示材料可供人工复核，不代表实盘授权。
- 仍不调用 `xttrader`，不下单，不查真实账户，不真实通知，不注册真实任务。

### 阶段五十二：最终只读锁定复核与归档一致性核验

- 下一阶段建议。
- 仍然不是实盘，不真实下单。
- 只能继续做最终只读锁定复核、归档一致性核验、人工闭环复查或更严格的灰度前检查。
- 仍不能自动 approve，不能调用 `xttrader`，不能查询真实账户，不能真实通知。

## Stage52 完成说明与 Stage53 预告

- 阶段五十二：最终只读锁定复核与归档一致性核验，新增 `qmt_ai_trading/live_lock_consistency/`、`scripts/run_live_lock_consistency.py` 和 `scripts/validate_stage52.ps1`，只读取 Stage48/49/50/51 本地证据并生成只读材料。
- Stage52 不等于实盘授权，不调用 `xttrader`，不真实下单，不查询真实资金/持仓/订单/成交，不真实发送通知。
- Stage53 建议为“最终只读归档核验与锁定材料复核”，仍只能继续做最终只读归档核验、锁定材料复核、人工闭环复查或更严格的灰度前检查。

## 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）

> Stage53 权威追加：本章节自 Stage53 起作为后续阶段提示词与验收的强制阅读内容。更新 roadmap 不代表打开实盘，不改变 Stage52 已完成状态，也不授予任何真实交易权限。

### 总体阶段口径与进度

- 后端 / 安全 / 灰度前核心链路暂定 60 阶段。
- 完整产品化闭环包含前端 UI，本项目总阶段调整为 75 阶段。
- 当前 Stage52 完成后，总体产品进度约 52/75 ≈ 69%。
- 后端核心链路进度约 52/60 ≈ 87%。
- UI 不作为绕过交易风控的入口。
- UI 只调用后端 API。
- UI 不能直接访问 QMT。
- UI 不直接访问 QMT。
- UI 不能直接下单。
- UI 不能绕过 Risk Gate。
- UI 不能绕过 Human Approval。
- UI 不能自动 approve。
- UI 默认不能开启 live。

### 完整阶段计划摘要

- Stage 1-22：基础交易工程闭环
- Stage 23-31：实盘前核心能力补齐
- Stage 32-40：最终授权、安全红线、灰度前封锁
- Stage 41-52：只读台账、签字、归档、锁定、一致性复核
- Stage 53-60：灰度前真实数据 / QMT dry-run / 小资金灰度准备
- Stage 61-75：前端 UI / 本地控制台 / 操作闭环

### Stage53-60 后端 / 安全 / 灰度前收尾计划

- Stage53：最终只读归档核验与锁定材料复核
- Stage54：灰度前最终缺口清零计划
- Stage55：QMT 实机 dry-run 环境最终校准
- Stage56：真实缓存质量复核与长期样本补齐
- Stage57：小资金灰度候选计划生成
- Stage58：小资金灰度前最终人工审批包
- Stage59：灰度执行开关隔离与双重确认机制
- Stage60：小资金灰度实盘预备验收

### Stage61-75 前端 UI 产品化计划

- Stage61：API Gateway 基础层
- Stage62：前端工程初始化
- Stage63：Dashboard 总览页面
- Stage64：行情缓存与数据质量 UI
- Stage65：Research / Strategy / ETF Rotation UI
- Stage66：Portfolio / Risk Gate UI
- Stage67：Human Approval UI
- Stage68：Paper Trading UI
- Stage69：Daily Pipeline / Scheduler UI
- Stage70：Backtest / Shadow Replay UI
- Stage71：报告中心 UI
- Stage72：灰度前安全审计 UI
- Stage73：系统设置 / 权限 / 审计日志 UI
- Stage74：UI 安全验收与端到端测试
- Stage75：本地控制台封版 / 可选桌面化

### UI 安全红线

- UI 只能作为后端 API 的操作界面和材料查看入口。
- UI 不能直接访问 QMT，也不能引入任何直接 QMT 交易调用。
- UI 不能直接下单，不能绕过 Risk Gate，不能绕过 Human Approval。
- UI 不能自动 approve，不能默认开启 live，不能把材料状态解释为实盘授权。
- UI 中任何“提交 / 确认 / 执行”动作都必须沿用后端已定义的风控、审批、dry-run / paper / gray 边界。

### 后续强制阅读规则

从 Stage53 起，任何新阶段 Codex 开发前，除原有 roadmap、architecture、最近阶段文档外，还必须阅读 `docs/qmt-ai-trading-project-roadmap.md` 中的“完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）”章节。
任何阶段提示词也必须确认：当前阶段是否属于 Stage1-60 后端/安全链路，还是 Stage61-75 UI 产品化链路。

### Stage53 完成说明与 Stage54 预告

Stage53 是“最终只读归档核验与锁定材料复核”，只生成最终只读归档核验包、锁定材料复核包、人工闭环复查包和下一阶段只读检查计划。`READY_FOR_ARCHIVE_VERIFICATION_REVIEW`、`NEED_MORE_EVIDENCE`、`NO_GO` 均只代表材料状态，不代表实盘授权。

Stage54 建议为“灰度前最终缺口清零计划”。Stage54 仍不能直接实盘，只能继续做灰度前最终缺口清零计划、补证项复核、人工闭环复查或更严格的灰度前检查；仍不能自动 approve，不能调用 `xttrader`，不能查询真实账户，不能真实通知。

### Stage54 完成说明：灰度前最终缺口清零计划

- Stage54 属于 Stage53-60：灰度前真实数据 / QMT dry-run / 小资金灰度准备，不属于 Stage61-75 UI 产品化阶段。
- Stage54 只生成灰度前最终缺口清零计划、补证项复核包、人工闭环复查包和下一阶段只读检查计划。
- Stage54 不等于实盘授权，不调用 `xttrader`，不真实下单，不查询资金/持仓/订单/成交，不真实发送通知。
- `READY_FOR_GAP_CLEARANCE_REVIEW` 只表示灰度前最终缺口清零计划材料可供人工复核，不代表实盘授权。
- 完整 Stage1-75 工程阶段计划与 Stage61-75 UI 产品化路线继续保留；UI 仍不能直接访问 QMT，不能绕过 Risk Gate，不能绕过 Human Approval，不能自动 approve。

### Stage55 预告：QMT 实机 dry-run 环境最终校准

- Stage55 仍不是实盘，不真实下单。
- Stage55 只在 Stage54 灰度前最终缺口清零计划基础上，校准 MiniQMT / QMT 客户端路径、`xtdata` 可用性、行情拉取能力、本地缓存写入、字段映射、交易日/时间字段和 ETF 标的白名单。
- Stage55 只允许使用 `xtdata`，不得调用 `xttrader`，不得查询真实资金、持仓、订单、成交，不得下单。

### Stage55 完成说明：QMT 实机 dry-run 环境最终校准

- Stage55 属于 Stage53-60：灰度前真实数据 / QMT dry-run / 小资金灰度准备，不属于 Stage61-75 UI 产品化阶段。
- Stage55 只生成 QMT 实机 dry-run 环境校准报告、xtdata 能力检查报告、ETF 白名单校准报告和 Stage56 真实缓存质量复核计划。
- Stage55 不等于实盘授权；只允许 xtdata 行情能力，不调用 `xttrader`，不真实下单，不查询资金/持仓/订单/成交，不真实发送通知。
- `READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW` 只表示 QMT 实机 dry-run 环境校准材料可供人工复核，不代表实盘授权。
- 完整 Stage1-75 工程阶段计划与 Stage61-75 UI 产品化路线继续保留；UI 仍不能直接访问 QMT，不能绕过 Risk Gate，不能绕过 Human Approval，不能自动 approve。

### Stage56 预告：真实缓存质量复核与长期样本补齐

- Stage56 仍不是实盘，不真实下单。
- Stage56 只在 Stage55 QMT 实机 dry-run 环境最终校准基础上，复核真实缓存覆盖率、缺失率、重复值、停牌/无成交处理、前复权/不复权一致性、成交量/成交额字段和长期样本完整性。
- Stage56 只允许使用 `xtdata` 或本地缓存，不得调用 `xttrader`，不得查询真实资金、持仓、订单、成交，不得下单。

### Stage56 完成说明：真实缓存质量复核与长期样本补齐

- Stage56 属于 Stage53-60：灰度前真实数据 / QMT dry-run / 小资金灰度准备，不属于 Stage61-75 UI 产品化阶段。
- 本阶段新增真实缓存质量复核、长期样本补齐计划、字段质量复核、下一阶段长期回测与绩效归因计划生成能力。
- 本阶段只允许本地缓存、mock provider dry-run fallback 和 `xtquant.xtdata` 只读行情能力。
- 本阶段不调用 `xttrader`，不导入 `XtQuantTrader`，不真实下单，不查询资金/持仓/订单/成交，不真实发送通知。
- `READY_FOR_REAL_CACHE_QUALITY_REVIEW` 只表示真实缓存质量复核与长期样本补齐材料可供人工复核，不代表实盘授权。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61：API Gateway 基础层至 Stage75：本地控制台封版 / 可选桌面化仍作为后续 UI 产品化路线，不在 Stage56 提前启动。
- UI 不直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。

### Stage57 预告：小资金灰度候选计划生成

- Stage57 仍然不是实盘，不真实下单。
- Stage57 仅在 Stage56 真实缓存质量复核与长期样本补齐基础上生成小资金灰度候选计划，包括灰度资金上限、单笔上限、单日上限、ETF 白名单、最大持仓数、最大回撤触发、熔断条件、人工审批流程和回滚流程。
- Stage57 不调用 `xttrader`，不查询真实资金、持仓、订单、成交，不下单。

### 阶段五十七完成说明：小资金灰度候选计划生成

- Stage57 属于 Stage53-60：灰度前真实数据 / QMT dry-run / 小资金灰度准备，不属于 Stage61-75 UI 产品化阶段。
- Stage57 只生成小资金灰度候选计划、灰度风险限制、人工审批清单、回滚与熔断计划、下一阶段审批包准备计划。
- Stage57 不等于实盘授权，不调用 `xttrader`，不真实下单，不查询资金、持仓、订单、成交，不真实发送通知。
- `READY_FOR_GRAY_CANDIDATE_REVIEW` 只表示小资金灰度候选计划材料可供人工复核，不代表实盘授权。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61：API Gateway 基础层至 Stage75：本地控制台封版 / 可选桌面化仍作为后续 UI 产品化路线，不在 Stage57 提前启动。
- UI 不直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。

### 阶段五十八预告：小资金灰度前最终人工审批包

- Stage58 仍属于灰度前准备阶段，仍不是实盘授权。
- Stage58 只在 Stage57 候选计划基础上生成最终人工审批包，包括资金上限、ETF 白名单、Risk Gate、Human Approval、回滚/熔断、日志/复盘和签字清单。
- Stage58 不调用 `xttrader`，不查询真实资金、持仓、订单、成交，不下单，不真实通知，不自动实盘。

### 阶段五十八补充：小资金灰度前最终人工审批包

- Stage58 属于 Stage53-60：灰度前真实数据 / QMT dry-run / 小资金灰度准备，不属于 Stage61-75 UI 产品化阶段。
- Stage58 在 Stage57 小资金灰度候选计划基础上生成最终人工审批包、资金与仓位审批表、Risk Gate / Human Approval 审批复核表、回滚与熔断审批表、最终签字清单和下一阶段只读封版计划。
- Stage58 不等于实盘授权，不调用 `xttrader`，不查询真实资金、持仓、订单、成交，不下单，不真实通知，不自动 approve。
- READY_FOR_FINAL_APPROVAL_REVIEW 只表示小资金灰度前最终人工审批包材料可供人工复核。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61：API Gateway 基础层至 Stage75：本地控制台封版 / 可选桌面化仍作为后续 UI 产品化路线，不在 Stage58 提前启动。
- UI 不直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。

### 阶段五十九预告：灰度前只读封版与运行前检查清单

- Stage59 仍不是实盘，不真实下单。
- Stage59 只在 Stage58 最终人工审批包基础上，生成灰度前只读封版包和运行前检查清单。
- Stage59 不调用 `xttrader`，不查询真实资金、持仓、订单、成交，不下单，不真实通知。

## Stage59 完成说明：灰度前只读封版与运行前检查清单

- Stage59 属于 Stage53-60：灰度前真实数据 / QMT dry-run / 小资金灰度准备，不属于 Stage61-75 UI 产品化阶段。
- Stage59 生成灰度前只读封版包、运行前 dry-run checklist、material manifest / sha256 摘要、最终签字状态复核和 Stage60 预灰度最终复核计划。
- Stage59 不代表实盘授权，不调用 `xttrader`，不查询真实资金、持仓、订单、成交，不下单，不真实发送通知，不自动 approve。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61-75 UI 产品化计划继续保留。UI 不直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。

## Stage60 预告：预灰度最终复核与 go/no-go 材料

- Stage60 仍属于 Stage53-60，不是 UI 产品化阶段，不直接实盘。
- Stage60 只基于 Stage59 只读封版材料做预灰度最终复核与 go/no-go 材料。
- Stage60 不调用 `xttrader`，不查询真实资金、持仓、订单、成交，不下单，不真实通知。

## Stage60 完成说明：预灰度最终复核与 go/no-go 材料

- Stage60 属于 Stage53-60：灰度前真实数据 / QMT dry-run / 小资金灰度准备，不属于 Stage61-75 UI 产品化阶段。
- Stage60 在 Stage59 灰度前只读封版基础上生成预灰度最终复核报告、material recheck、go/no-go 草案、no-go blockers、go conditions 和 Stage61 API Gateway 衔接计划。
- Stage60 不代表实盘授权，GO_DRAFT 不代表实盘授权，READY_FOR_PRE_GRAY_FINAL_REVIEW 只表示材料可供人工复核。
- Stage60 不调用 `xttrader`，不查询真实资金、持仓、订单、成交，不下单，不真实发送通知，不自动 approve。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61-75 UI 产品化计划继续保留。UI 不直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。

## Stage61 预告：API Gateway 基础层

- Stage61 进入 Stage61-75 UI 产品化路线，但仍不是实盘阶段。
- Stage61 只搭建本地 API Gateway 基础边界和只读查询接口。
- Stage61 不允许 UI 直接访问 QMT，不能绕过 Risk Gate，不能绕过 Human Approval，不能自动 approve。
- Stage61 不调用 `xttrader`，不查询真实资金、持仓、订单、成交，不下单。

## Stage61 完成说明：API Gateway 基础层

- Stage61 进入 Stage61-75 UI 产品化路线，新增本地只读 API Gateway 基础边界。
- Stage61 不等于实盘授权；不调用 `xttrader`，不查询真实资金、持仓、订单、成交，不下单，不发送真实通知。
- API Gateway 默认绑定 `127.0.0.1`，只提供健康检查、阶段状态、roadmap/architecture 摘要、Stage55-60 报告摘要、latest validation log 摘要、manifest、scheduler preview、safety boundary 和 capability 查询。
- UI 仍不能直接访问 QMT，不能绕过 Risk Gate，不能绕过 Human Approval，不能自动 approve。
- Stage62 预告：本地控制台报告读取层，仍不得直接实盘。

### Stage62 完成说明：本地控制台报告读取层

- Stage62 进入 Stage61-75 UI 产品化路线，但仍不是实盘阶段。
- Stage62 新增本地控制台报告读取层，仅生成本地只读报告包、控制台路由索引、Stage55-61 报告列表、latest validation log 摘要、manifest 摘要、scheduler preview 摘要和 safety boundary。
- READY_FOR_LOCAL_CONSOLE_REVIEW 只表示本地控制台报告读取层材料可供人工复核，不代表实盘授权。
- Stage62 不调用 xttrader，不查询真实资金/持仓/订单/成交，不真实下单，不真实发送通知，不自动 approve。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61-75 前端 UI 产品化计划继续保留。
- UI 仍不能直接访问 QMT，UI 不能绕过 Risk Gate，UI 不能绕过 Human Approval，UI 不能自动 approve。

### Stage63 预告：本地控制台报告详情页与过滤层

- Stage63 基于 Stage62 本地控制台报告读取层，增加报告详情页、阶段筛选、状态筛选、warning/blocking reason 过滤、manifest 文件详情、validation log 摘要详情。
- Stage63 仍不是实盘，不真实下单，不调用 xttrader，不查询真实资金/持仓/订单/成交，不允许 UI 直接访问 QMT，不允许绕过 Risk Gate，不允许绕过 Human Approval，不允许自动 approve。

## Stage63 完成说明：本地控制台报告详情页与过滤层

Stage63 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。本阶段在 Stage62 本地控制台报告读取层基础上追加只读详情页模型、详情路由索引、阶段/状态/severity 过滤、warning/blocking reason 过滤、manifest detail、validation log detail 和下一阶段 Stage64 控制台概览面板计划。

Stage63 不等于实盘授权；不调用 `xttrader`，不查询真实账户，不下单，不真实发送通知，不自动 approve，不绕过 Risk Gate / Human Approval。`READY_FOR_LOCAL_CONSOLE_DETAIL_REVIEW` 只表示本地控制台报告详情页与过滤层材料可供人工复核。

Stage64 预告：阶段六十四为本地控制台概览面板层，仍不得直接实盘，UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## Stage64 追加完成说明：本地控制台概览面板层

Stage64 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage64 基于 Stage63 本地控制台报告详情页与过滤层，新增本地控制台概览面板层的只读数据模型、dashboard card index、stage status cards、latest validation card、warning/blocking stats、manifest/hash status、scheduler preview status、safety boundary status、API capability card、detail/filter card 与 Stage65 控制台 shell 计划。

Stage64 不等于实盘授权；不调用 `xttrader`；不查询真实账户；不真实下单；不发送真实通知；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

Stage65 预告：本地控制台 shell / 静态页面骨架层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。

### Stage65 完成说明：本地控制台 shell / 静态页面骨架层

Stage65 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage65 基于 Stage64 本地控制台概览面板层新增本地静态控制台 shell、`index.html` / `app.js` / `style.css` 页面骨架、shell manifest、route map、asset index、data binding placeholders、static safety boundary、tolerant reader 与 Stage66 数据绑定计划。

Stage65 不等于实盘授权；不调用 `xttrader`；不查询真实账户；不真实下单；不发送真实通知；不自动 approve；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。`READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW` 只表示本地控制台 shell / 静态页面骨架层材料可供人工复核。

Stage66 预告：阶段六十六为本地控制台静态数据绑定层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。

### 阶段六十六：本地控制台静态数据绑定层（已完成）

- Stage66 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。
- 基于 Stage65 静态 shell，将 Stage64 dashboard cards、Stage63 detail/filter、Stage62 report list、Stage61 API capability、latest validation summary、manifest/hash、scheduler preview 与 safety boundary 绑定为本地静态只读数据包。
- `READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW` 只表示本地控制台静态数据绑定层材料可供人工复核，不代表实盘授权。
- UI 继续不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。
- Stage66 不调用 `xttrader`，不查询真实账户，不真实下单，不发送真实通知。

### 阶段六十七：本地只读预览服务层（预告）

- Stage67 基于 Stage66 静态数据绑定层，提供本地只读预览服务或静态文件服务。
- 只绑定 `127.0.0.1`，默认 dry-run，只读，不提供 POST/PUT/PATCH/DELETE，不访问 QMT，不查询真实账户，不发通知，不下单。

### Stage67 完成说明：本地只读预览服务层

- Stage67 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。
- Stage67 只提供本地 `127.0.0.1:8767` 静态文件只读预览服务，默认 dry-run/read-only。
- Stage67 不等于实盘授权，不调用 `xttrader`，不查询真实账户，不下单，不真实发送通知，不自动 approve。
- `READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW` 只表示本地只读预览服务层材料可供人工复核。
- 完整 Stage1-75 工程阶段计划与 Stage61-75 前端 UI 产品化路线继续保留；UI 仍不能直接访问 QMT，不能绕过 Risk Gate，不能绕过 Human Approval，不能自动 approve。

### Stage68 预告：本地控制台刷新与导航增强层

Stage68 将基于 Stage67 本地只读预览服务增强页面导航、只读刷新按钮、hash route 切换、错误占位、数据更新时间显示和本地静态 bundle 重载体验；仍不得直接实盘，不调用 `xttrader`，不查询真实资金、持仓、订单、成交，不下单。

### Stage68 完成说明：本地控制台刷新与导航增强层

- Stage68 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。
- Stage68 基于 Stage67 本地只读预览服务层，新增本地静态控制台刷新按钮、hash route 导航、bundle reload、latest updated 显示、loading / error / empty state 占位、前端安全分类和 Stage69 状态分组与筛选体验计划。
- Stage68 不等于实盘授权；不调用 `xttrader`；不查询真实账户；不真实下单；不发送真实通知；不自动 approve；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61-75 前端 UI 产品化计划继续保留。
- Stage69 预告：阶段六十九为本地控制台状态分组与筛选体验层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。

### Stage69 完成说明：本地控制台状态分组与筛选体验层

- Stage69 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。
- Stage69 基于 Stage68 本地控制台刷新与导航增强层，新增本地静态控制台 status / severity / stage 分组、warning 与 blocking reason 筛选、只读搜索、卡片折叠/展开、分组计数 badge、筛选 empty state、forbidden route 安全占位与 Stage70 报告详情钻取与导出计划。
- Stage69 不等于实盘授权；不调用 `xttrader`；不查询真实账户；不真实下单；不发送真实通知；不自动 approve；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61-75 前端 UI 产品化计划继续保留。
- Stage70 预告：阶段七十为本地控制台报告详情钻取与导出层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。

## 阶段七十：本地控制台报告详情钻取与导出层（已完成）

阶段七十属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage70 在 Stage69 状态分组与筛选体验层之后，新增本地静态控制台报告详情钻取、单报告预览、复制摘要、导出本地 Markdown/JSON 复核快照、错误报告定位、人工复核包入口、report detail route map、export manifest、copy/export safety report、forbidden hash route 安全占位和 Stage71 人工复核工作台计划。

Stage70 不是实盘授权，不调用 `xttrader`，不调用 QMT 交易接口，不真实下单，不查询真实账户/资金/持仓/订单/成交，不真实发送通知，不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW 只表示本地控制台报告详情钻取与导出层材料可供人工复核。

阶段七十一预告：本地控制台人工复核工作台层。Stage71 仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单；它将基于 Stage70 报告详情钻取与导出层增加人工复核工作台、复核清单、只读 review notes 模板、本地确认项列表和复核包目录索引。

### Stage71 完成说明：本地控制台人工复核工作台层

- Stage71 属于“完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）”中的 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。
- Stage71 只生成本地只读人工复核工作台、review checklist、review notes template、local confirmation checklist、review package index、review safety report 和 Stage72 UI 验收汇总层计划。
- Stage71 不等于实盘授权，不调用 xttrader，不查询真实账户，不下单，不发送真实通知，不自动 approve。
- UI 继续不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。
- Stage72 预告：本地控制台 UI 验收汇总层，仍不得直接实盘。

### Stage72 完成说明：本地控制台 UI 验收汇总层

- Stage72 属于“完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）”中的 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。
- Stage72 只生成本地只读 UI 验收汇总、页面清单、功能清单、安全清单、未完成项、验收结论草稿、验收包索引、route coverage、asset coverage、UI safety summary 和 Stage73 本地文档/帮助层计划。
- Stage72 不等于实盘授权，不调用 xttrader，不查询真实账户，不下单，不发送真实通知，不自动 approve。
- UI acceptance summary / acceptance conclusion draft 都不是审批授权；READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW 只表示本地控制台 UI 验收汇总层材料可供人工复核。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61-75 前端 UI 产品化计划继续保留。UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。
- Stage73 预告：本地文档/帮助层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。

### Stage73 完成说明：本地文档/帮助层

- Stage73 属于“完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）”中的 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。
- Stage73 只生成本地只读帮助首页、页面说明、功能说明、安全说明、FAQ、错误处理说明、术语表、route help map、help package index、docs safety report 和 Stage74 本地演示打包层计划。
- Stage73 不等于实盘授权，不调用 xttrader，不查询真实账户，不下单，不发送真实通知，不自动 approve。
- help docs / FAQ / glossary 都不是审批授权；READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW 只表示本地文档/帮助层材料可供人工复核。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61-75 前端 UI 产品化计划继续保留。UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。
- Stage74 预告：本地演示打包层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。

### 阶段七十四：本地演示打包层（已完成）

- Stage74 属于“完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）”中的 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。
- Stage74 基于 Stage73 本地文档/帮助层，新增本地静态演示包目录、静态资源清单、演示入口页、演示说明、只读 demo manifest、demo route map、demo asset manifest、demo package index、demo safety report、demo validation summary 与 Stage75 UI 产品化收口计划。
- Stage74 不等于实盘授权，不调用 xttrader，不查询真实账户，不下单，不发送真实通知，不自动 approve。
- demo guide / manifest / package index 都不是审批授权；READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW 只表示本地演示打包层材料可供人工复核。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61-75 前端 UI 产品化计划继续保留。UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。
- Stage75 预告：阶段七十五为 UI 产品化收口层，仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。

### 阶段七十五：UI 产品化收口层（已完成）

- Stage75 属于“完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）”中的 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。
- Stage75 基于 Stage74 本地演示打包层，新增 UI 产品化阶段总览、UI 能力矩阵、安全边界总表、只读演示入口汇总、页面/路由覆盖总览、静态资产覆盖总览、风险与限制总览、最终验收结论草稿、UI 产品化收口报告与 Stage76 路线重审建议。
- Stage75 不等于实盘授权，不调用 xttrader，不查询真实账户，不下单，不发送真实通知，不自动 approve。
- closure report / capability matrix / final conclusion draft 都不是审批授权；READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW 只表示 UI 产品化收口层材料可供人工复核。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61-75 前端 UI 产品化计划继续保留。UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。
- Stage76 建议：路线重审与下一轮开发计划层；先复盘 Stage1-75 已完成内容、当前缺口、安全边界、数据质量与 UI 成熟度，不直接进入实盘。

### 阶段七十六：路线重审与下一轮开发计划层（已完成）

- Stage76 在 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线收口之后执行，只做路线重审、架构复盘、安全边界复盘、缺口清单和下一轮开发计划。
- Stage76 不等于实盘授权，不调用 xttrader，不查询真实账户，不下单，不发送真实通知，不自动 approve。
- Stage76 明确 Stage75 UI 产品化收口不等于实盘授权；READY_FOR_NEXT_ROADMAP_REVIEW 只表示路线重审材料可供人工复核。
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留；Stage61-75 前端 UI 产品化计划继续保留。UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。
- Stage77 预告：阶段七十七为实盘前安全审计重启与真实数据质量复核层，仍不得直接实盘，不调用 xttrader，不查询真实资金、持仓、订单、成交，不下单。

## Stage77 纠偏说明：业务控制台 MVP 与任务编排 API 层

Stage77 不再继续开发只读项目验收台，而是转向本地业务控制台 MVP：通过 localhost-only API 触发白名单 dry-run / shadow / read-only 任务，覆盖总览、行情数据、选股、策略、Agent 投研、回测、风控、报告、任务中心和系统设置。Stage77 不接实盘、不查询真实账户、不下单、不调用 xttrader、不自动 approve。

## Stage78 预告：实盘前安全审计重启与真实数据质量复核层

Stage78 仍然不是实盘，将基于 Stage77 业务控制台 MVP 重新启动实盘前安全审计，并重点复核真实缓存质量、QMT xtdata 稳定性、Paper Trading 成熟度、异常监控、live config 多重确认和数据质量报告。

### 阶段七十八：AI 接口配置、模型发现与压力测试层

Stage78 在业务控制台中新增 AI 模型配置中心，支持用户填写 OpenAI-compatible Base URL / API Key、查询模型列表、模型多选、执行 1000/3000/5000 字串行压力测试，并保存 Agent 模型用途映射草稿。密钥只在本地后端会话请求中使用，不提交、不写 localStorage、不进入报告明文。本阶段只服务 Agent 能力配置，不接交易、不调用 xttrader、不查账户、不下单。

### 阶段七十九预告：因子研究工作台与选股评分可视化层

Stage79 将把 Research / Factor Engineering 能力做成前端可见、可配置、可运行、可复盘的业务模块，仍然 dry-run / shadow，不接实盘、不真实下单。

### 阶段七十九：因子研究工作台与选股评分可视化层 + 验收日志落盘修复

- 当前状态：已完成。
- 建设因子研究工作台，提供默认因子目录、配置种子、factor_scan、IC / RankIC 评估、候选池与前端可视化。
- 追加 `run_qmt_tasks.ps1` 验收日志落盘修复模板，确保后续可生成 `validation_logs/stage*_validation_*.log`。
- 仍不接实盘、不下单、不查询真实账户、不调用 xttrader、不自动 approve。

### 阶段八十预告：因子候选池到 Strategy Engine dry-run TradeIntent 联调层

- 将 Stage79 `factor_candidates` 接入 Strategy Engine，生成 dry-run TradeIntent，并继续经过 Risk Gate。
- 仍然不是实盘，不真实下单。
