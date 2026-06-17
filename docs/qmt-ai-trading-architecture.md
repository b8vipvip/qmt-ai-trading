# qmt-ai-trading 长期架构说明

本项目继续使用原有 qmt-ai-trading 作为主系统，不再使用 DeltaFStation / cn-trader 作为底座。

原因：
- 当前 qmt-ai-trading 已经跑通国金证券 QMT 接口和部分基础逻辑。
- 不希望重新迁移到另一个底座，避免重复改造。
- 后续 UI 设计应建立在本项目后端功能稳定之后，而不是先套现成 UI。
- 本项目目标是逐步融合 TradingAgents、Qlib、vn.py / VeighNa 的核心优点，而不是直接把这些项目硬合并。

## 一、系统定位

qmt-ai-trading 是面向中国 A 股 / ETF 的 AI Agent 辅助量化交易系统。

核心原则：

1. QMT 是最终交易执行终端。
2. AI Agent 只做分析、解释、评分和建议，不允许绕过风控直接下单。
3. 研究层负责生成可验证的信号，不依赖 LLM 主观判断直接交易。
4. 实盘前必须经过硬风控 Risk Gate。
5. UI 放到后续阶段，根据已经稳定的后端模块设计。
6. 所有实盘功能默认关闭，先 dry-run / shadow / paper，再小仓位人工确认。

## 二、总架构

```text
qmt-ai-trading 主系统
│
├─ 1. QMT Gateway 执行层
│   ├─ xtdata 行情
│   ├─ xttrader 查询资金/持仓/委托
│   ├─ 模拟下单 / 实盘下单
│   └─ 实盘前强风控拦截
│
├─ 2. Data Hub 数据层
│   ├─ QMT 本地行情
│   ├─ AkShare / Tushare / BaoStock
│   ├─ 指数成分、ETF、行业、财务、新闻
│   └─ parquet / duckdb / sqlite / postgres
│
├─ 3. Qlib / vnpy.alpha 研究层
│   ├─ 因子工程
│   ├─ Alpha158 / Alpha360 / Alpha101
│   ├─ LightGBM / Lasso / MLP
│   ├─ 回测
│   └─ 模型评分与信号生成
│
├─ 4. TradingAgents Agent 分析层
│   ├─ 技术面 Agent
│   ├─ 基本面 Agent
│   ├─ 情绪/新闻 Agent
│   ├─ 多空辩论 Agent
│   ├─ 风险 Agent
│   └─ 组合经理 Agent
│
├─ 5. Strategy Engine 策略层
│   ├─ ETF 轮动
│   ├─ 多因子选股
│   ├─ 仓位计算
│   └─ buy/sell/hold 结构化信号
│
└─ 6. Risk Gate 风控闸门
    ├─ T+1
    ├─ 100股整数倍
    ├─ 涨跌停
    ├─ 最大单票仓位
    ├─ 最大日亏损
    ├─ 最大回撤
    ├─ 禁止黑名单股票
    └─ 实盘二次确认
三、各模块职责边界
1. QMT Gateway 执行层

目标：统一封装 QMT / xtquant 调用。

职责：

读取行情。
查询账户资金。
查询持仓。
查询委托。
查询成交。
提交模拟委托。
提交实盘委托。
撤单。
记录订单生命周期。

要求：

QMT Gateway 不做策略判断。
QMT Gateway 不做 AI 分析。
QMT Gateway 只接受 Strategy Engine 和 Risk Gate 已经批准的结构化指令。
实盘下单函数必须默认关闭，必须通过显式配置开启。

建议目录：

qmt_ai_trading/
├─ gateway/
│  ├─ qmt_market.py
│  ├─ qmt_account.py
│  ├─ qmt_order.py
│  ├─ qmt_position.py
│  └─ qmt_types.py
2. Data Hub 数据层

目标：建立统一数据入口，避免每个策略自己乱调数据源。

职责：

统一证券代码格式。
统一交易日历。
统一行情数据。
统一指数、ETF、行业、财务、新闻数据。
支持 QMT 本地行情。
后续支持 AkShare / Tushare / BaoStock。
支持本地缓存。

要求：

策略层只能通过 Data Hub 取数据。
Agent 层只能通过 Data Hub 取数据。
数据层不直接下单。
数据源失败时必须有降级或错误提示。

建议目录：

qmt_ai_trading/
├─ datahub/
│  ├─ symbols.py
│  ├─ calendar.py
│  ├─ market_data.py
│  ├─ etf_data.py
│  ├─ fundamentals.py
│  ├─ news_data.py
│  └─ cache.py
3. Research 研究层

目标：吸收 Qlib / vnpy.alpha 的核心优点，但不直接重写成 Qlib 或 vn.py。

提取的核心能力：

因子工程。
Alpha158 / Alpha360 / Alpha101 思路。
IC / RankIC。
回测评价。
模型训练。
模型滚动评估。
策略信号验证。

要求：

Research 只输出评分、预测值、候选池、回测报告。
Research 不直接下单。
Research 不直接调用 QMT order。
所有模型输出必须能被回测验证。

建议目录：

qmt_ai_trading/
├─ research/
│  ├─ factors.py
│  ├─ alpha158.py
│  ├─ alpha101.py
│  ├─ dataset.py
│  ├─ train_model.py
│  ├─ evaluate_model.py
│  └─ backtest_report.py
4. TradingAgents Agent 分析层

目标：借鉴 TradingAgents / TradingAgents-CN 的多智能体投研流程，但不直接复制其 UI 或整个项目。

Agent 分工：

技术面 Agent。
基本面 Agent。
新闻 / 情绪 Agent。
多头研究员。
空头研究员。
风险 Agent。
组合经理 Agent。

要求：

Agent 只输出结构化建议。
Agent 不允许直接调用实盘下单。
Agent 不允许绕过 Risk Gate。
Agent 不允许生成后自动执行任意 Python 策略代码。
LLM 输出必须转成 JSON 或明确结构化格式。
LLM 建议必须带 reasons、risk_flags、confidence。

建议输出格式：

{
  "symbol": "159915.SZ",
  "signal": "HOLD",
  "confidence": 0.61,
  "score": 72,
  "max_position_pct": 0.15,
  "reasons": [
    "ETF 近期动量强于基准",
    "短期波动率偏高，暂不满足加仓条件"
  ],
  "risk_flags": [
    "单一 ETF 集中度偏高",
    "近期回撤未完全修复"
  ]
}

建议目录：

qmt_ai_trading/
├─ agents/
│  ├─ base_agent.py
│  ├─ technical_agent.py
│  ├─ fundamental_agent.py
│  ├─ sentiment_agent.py
│  ├─ bull_bear_debate.py
│  ├─ risk_agent.py
│  └─ portfolio_manager.py
5. Strategy Engine 策略层

目标：承接数据层、研究层、Agent 层结果，形成统一交易信号。

当前优先方向：

ETF 轮动。
大盘择时。
多因子选股。
仓位计算。
buy / sell / hold 信号生成。

要求：

Strategy Engine 输出结构化 TradeIntent。
Strategy Engine 不直接实盘下单。
下单前必须经过 Risk Gate。
所有策略必须支持 dry-run。
所有策略必须记录当日信号、原因、数据快照。

建议目录：

qmt_ai_trading/
├─ strategies/
│  ├─ etf_rotation.py
│  ├─ multi_factor_stock.py
│  ├─ timing.py
│  └─ position_sizing.py

建议 TradeIntent：

{
  "symbol": "510300.SH",
  "side": "BUY",
  "target_percent": 0.2,
  "quantity": 1000,
  "price_type": "LATEST",
  "reason": "ETF rotation score ranked top 1",
  "source": "strategy_engine",
  "dry_run": true
}
6. Risk Gate 风控闸门

目标：所有下单必须经过 Risk Gate。

风控规则：

A 股 T+1。
100 股整数倍。
涨跌停过滤。
停牌过滤。
ST / 黑名单过滤。
单票最大仓位。
单行业最大仓位。
单日最大亏损。
最大回撤。
最大换手率。
实盘二次确认。
禁止 LLM 直接下单。

要求：

Risk Gate 是实盘前最后一道硬门。
Risk Gate 拒绝后必须写明原因。
任何模块不得绕过 Risk Gate 调 QMT 实盘下单。
实盘默认关闭。

建议目录：

qmt_ai_trading/
├─ risk/
│  ├─ rules.py
│  ├─ position_limit.py
│  ├─ trade_validator.py
│  ├─ live_gate.py
│  └─ blacklist.py
四、推荐分阶段开发路线
阶段一：项目安全和结构基线

目标：

保留现有已跑通的 QMT 接口和基础逻辑。
新增架构目录，但不大规模改动原代码。
增加配置安全。
增加同步脚本。
增加 dry-run 默认保护。
明确禁止默认实盘。

阶段一验收：

项目可以正常启动。
原有 QMT 基础逻辑不被破坏。
GitHub 同步脚本可用。
不提交 .env、Token、密码、数据库文件。
新增 docs 文档。
新增基础目录结构。
py -m compileall 能通过。
阶段二：QMT Gateway 标准化

目标：

把当前分散的 QMT 调用整理成 gateway 层。
统一账户、行情、持仓、委托、成交接口。
输出统一数据结构。
保留原逻辑兼容入口。
阶段三：Risk Gate

目标：

所有模拟/实盘委托都经过 Risk Gate。
增加 T+1、100 股整数、涨跌停、仓位、黑名单、最大亏损规则。
实盘下单默认关闭。
增加人工确认模式。
阶段四：Strategy Engine

目标：

完成 ETF 轮动策略结构化。
输出 TradeIntent。
支持 dry-run。
支持回测 / 影子盘 / 实盘前确认。
阶段五：Research 研究层

目标：

引入 Qlib / vnpy.alpha 思路。
增加因子工程。
增加模型训练与评价。
先服务 ETF / 指数，再扩展到股票池。
阶段六：TradingAgents 分析层

目标：

引入多 Agent 投研流程。
输出结构化建议。
与 Strategy Engine 和 Risk Gate 解耦。
不允许 Agent 直接下单。
阶段七：UI

目标：

根据已经稳定的后端功能设计 UI。
页面包括：
仪表盘。
QMT 连接状态。
资金 / 持仓。
策略信号。
风控拦截记录。
Agent 投研报告。
dry-run / shadow 交易日志。
实盘确认面板。
五、明确不做的事情
不再把 DeltaFStation 作为主系统底座。
不把 TradingAgents-CN 整个项目直接塞进来。
不把 Qlib 整个项目改造成主系统。
不把 vn.py 整个项目作为主系统重写。
不允许 LLM 直接调用实盘下单。
不允许上传策略后在 Web 进程里无隔离执行任意代码。
不提交真实 API Key、数据库密码、券商账号、QMT 路径、Token。
不在阶段一做复杂 UI。
不在没有回测、风控、人工确认前开启自动实盘。
六、给 Codex 的长期约束

后续 Codex 修改本项目时，必须遵守：

优先保护现有已跑通的 QMT 逻辑。
每次修改前先阅读本文件。
不要引入新的主系统底座。
不要默认开启实盘下单。
新增模块必须遵守分层边界。
Agent 只能输出建议，不得直接下单。
所有实盘相关代码必须经过 Risk Gate。
所有配置必须从环境变量或本地配置文件读取。
不能把 .env、密钥、Token、数据库、账号密码提交到 GitHub。
修改后必须运行基础检查，再提交。



## 阶段四进度：ETF Rotation Strategy Engine

阶段四已建立 ETF Rotation Strategy Engine 标准接口：现有 ETF universe、评分、shadow replay 和 dry-run 研究逻辑继续保留，策略层新增标准化候选、选择和信号生成入口。ETF 轮动策略只输出 `TradeIntent` 或 `list[TradeIntent]`，默认 dry-run，不直接下单，不调用真实 QMT `order_stock`。

下单职责仍保持在 `TradeIntent -> Risk Gate -> QMT Gateway` 链路中：Strategy Engine 负责生成结构化意图，Risk Gate 负责风控校验，QMT Gateway 负责受控执行。

## 阶段五进度：Data Hub 标准化

阶段五已追加 Data Hub 标准化基线：`datahub.symbols` 统一 A 股/ETF 代码到 `510300.SH` / `159915.SZ` 格式；`datahub.models` 提供轻量 dataclass 数据契约；`datahub.market_data` 通过 QMT 只读 gateway adapter 懒加载行情，在无真实数据时返回 `None` 或空列表；`datahub.etf_universe` 提供离线默认 ETF 候选池；`datahub.cache` 保留本地缓存接口占位但不写入敏感路径。ETF Rotation Strategy Engine 新增从 Data Hub ETF universe 构造候选的 adapter，Strategy、Research、Agent 后续应通过 Data Hub 统一取数。

## 阶段六进度：Research 层标准化

阶段六新增轻量 Research 层接口，覆盖因子计算、研究评分、研究报告和 ETF 轮动策略适配。当前实现只消费 Data Hub 已提供的 `MarketBar` 数据，不连接网络、不连接 QMT、不生成订单。

新增能力包括：

- `qmt_ai_trading.research.factors`：提供动量、波动率、成交量因子和因子结果排序。
- `qmt_ai_trading.research.scoring`：提供 `ResearchScore`、单标的评分和 ETF universe 批量评分。
- `qmt_ai_trading.research.report`：提供结构化研究报告和可读文本摘要。
- ETF Rotation Strategy 新增 ResearchScore 到 ETFCandidate 的只读 adapter，后续 TradeIntent 仍走原有策略流程。

阶段六仍不接完整 Qlib / vn.py 依赖，不做 UI，不接实盘；下单链路继续要求经过 Risk Gate + QMT Gateway。

## 阶段七：Research Model Lab（已完成）

阶段七新增轻量 Research Model Lab，覆盖 ETF / 指数研究所需的样本构造、特征矩阵、forward return 标签、train/test 切分、IC / RankIC / directional accuracy 和简单 baseline 模型评价。

新增模块包括：

- `qmt_ai_trading.research.dataset`：提供 `FeatureRow`、`LabelRow`、`ResearchDataset`、`TrainTestSplit` 以及从 `MarketBar` 构造样本和标签的纯 Python helper。
- `qmt_ai_trading.research.metrics`：提供 Pearson IC、Spearman RankIC、方向准确率和统一评价结果结构。
- `qmt_ai_trading.research.model_lab`：提供轻量 baseline 训练、预测和 `run_model_lab(...)` 入口。

Research Score 新增 Model Lab prediction adapter，ETF Rotation Strategy 可选接入 Model Lab 结果，但输出仍保持为 `ETFCandidate` 或 dry-run `TradeIntent`。Model Lab 不连接网络、不连接 QMT、不直接下单；Strategy 使用其结果时仍必须经过 Risk Gate + QMT Gateway。

## Stage 8: Backtest / Shadow Replay 标准化

阶段八新增轻量级 Backtest / Shadow Replay 层，用于把 ETF Strategy、Research、Model Lab 产生的 dry-run `TradeIntent` 输入到历史回放和模拟成交流程中，输出 `BacktestResult` / `ShadowReplayResult`、交易日志、equity curve 以及 total_return / max_drawdown / win_rate 等基础指标。

该层仅处理模拟订单、模拟成交和模拟资产，不连接真实 QMT，不调用真实下单接口，不绕过 Risk Gate + QMT Gateway 的真实交易边界。当前实现是 baseline，不是完整撮合引擎，后续可继续接入现有 shadow replay / dry-run 日志 adapter。

## Stage 9: Signal Pipeline / Daily Runner 标准化

阶段九新增 `qmt_ai_trading.pipeline`，用于把 Data Hub 默认 ETF universe、ETF Rotation Strategy、Risk Gate、Backtest / Shadow Replay 串成统一的每日 dry-run / shadow 编排流程。Pipeline 输出 `PipelineResult` 和文本日报，记录每一步 `PipelineStepResult`，空数据或单步失败时保持结构化返回。

当前阶段不连接真实 QMT 下单，不调用 `qmt_order.place_order`，不写入真实订单；所有生成的 `TradeIntent` 默认 `dry_run=True` 并必须经过 `validate_trade_intent`。命令行入口 `scripts/run_daily_pipeline.py` 可用于本地 dry-run 日报输出，后续可继续接计划任务、Windows Task Scheduler、UI 或消息通知。

## 阶段十进度：Report / Notification 输出层标准化

Stage 10 新增 `qmt_ai_trading.reporting` 输出层，将 Daily Pipeline 的 `PipelineResult` 输出为 Markdown、JSON、HTML 三类离线报告。默认报告目录为 `reports/YYYY-MM-DD/`，报告产物通过 `.gitignore` 忽略，不纳入版本控制。

本阶段同时新增 Email、Telegram、WeCom 通知适配器占位接口。所有通知保持 dry-run，不读取真实 Token，不连接外部通知服务，不发送真实消息。该阶段不接实盘、不调用真实 QMT 下单、不做 UI，仅为后续安全接入通知能力预留接口。

## 阶段十一进度：Windows Task Scheduler 标准化

Stage 11 新增 `qmt_ai_trading.scheduler` 本地调度层，用于生成 Windows Task Scheduler 注册、删除和查询命令，并提供默认 dry-run 保护。默认任务名为 `QmtAiTradingDailyDryRun`，默认 15:30 运行，计划任务入口为 `scripts/run_scheduled_daily_pipeline.py`。

该阶段默认执行 dry-run / shadow daily pipeline，生成 `reports/` 本地报告并写入 `logs/daily_pipeline/` 日志；注册和删除脚本在不传 `--execute` 时只打印 `schtasks` 预览命令，不实际修改系统计划任务。Stage 11 不真实下单、不真实发送通知、不连接真实 QMT 下单链路，后续可继续接 UI 或手动确认流程。
