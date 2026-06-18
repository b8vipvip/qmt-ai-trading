# qmt-ai-trading 项目总路线文档

> 后续每个阶段开发前必须先阅读本文档，再阅读 `docs/qmt-ai-trading-architecture.md`，再阅读对应上一阶段文档。

## 1. 项目定位

qmt-ai-trading 是个人本地 A股 / ETF / QMT / AI Agent 辅助量化系统。系统默认 dry-run / shadow，风控优先，AI 不直接下单，QMT Gateway 是唯一真实交易边界，当前仍未开启实盘。

## 2. 总体架构路线

总体路线为 DataHub → LocalBarStore → Provider 抽象 → QMT Historical Provider → Research → Model Lab → ETF Strategy → TradeIntent → Risk Gate → Backtest / Shadow Replay → Pipeline → Reporting → Scheduler → 未来 Agent / Human Approval / Live Trading。任何交易相关能力都必须保持分层边界，Research、Model Lab 与 Agent 只能产出建议或 TradeIntent。

## 3. 已完成阶段一到十五

| 阶段 | 阶段目标 | 主要模块 | 当前状态 | 关键验收点 |
| --- | --- | --- | --- | --- |
| 一 | 项目安全和结构基线 | 目录、配置、敏感信息规则 | 已完成 | Git 忽略敏感文件与运行产物 |
| 二 | QMT Gateway 标准化 | gateway、模型、安全边界 | 已完成 | 网关成为唯一交易边界 |
| 三 | Risk Gate 完整化 | risk rules、trade validator | 已完成 | 交易意图必须先过风控 |
| 四 | ETF 轮动 Strategy Engine 标准化 | ETF rotation、scoring | 已完成 | 策略输出标准化信号 |
| 五 | Data Hub 标准化 | datahub models/providers | 已完成 | 数据访问抽象统一 |
| 六 | Research 层标准化 | research dataset/factors/report | 已完成 | 研究层与交易层解耦 |
| 七 | Research Model Lab | model_lab、metrics | 已完成 | 模型实验不触达实盘 |
| 八 | Backtest / Shadow Replay 标准化 | backtest、shadow replay | 已完成 | 回测和影子复盘可运行 |
| 九 | Signal Pipeline / Daily Runner 标准化 | pipeline daily runner | 已完成 | 日常 dry-run pipeline 可执行 |
| 十 | Report / Notification 输出层标准化 | reporting writer/notifier | 已完成 | 通知默认 dry-run |
| 十一 | Windows Scheduler 本地调度标准化 | scheduler、register scripts | 已完成 | 计划任务默认 dry-run 预览 |
| 十二 | Historical Data Cache / Local Market Data Store | LocalBarStore | 已完成 | 本地历史行情缓存可读写 |
| 十三 | QMT Historical Provider Adapter | qmt_provider | 已完成 | QMT 历史数据适配可选接入 |
| 十四 | QMT Historical Provider 实机联调 + 数据字段校准 | diagnostics、field mapping | 已完成 | 字段映射和诊断脚本可用 |
| 十五 | QMT 历史数据自动补全接入 Scheduler | cache_warmup、scheduled pipeline | 已完成 | warmup_cache 支持 mock/qmt 且无 xtquant 不崩溃 |

## 4. 当前安全边界

- 不提交 `.env` / token / key / 数据库 / 缓存 / reports / logs。
- 不修改 `scripts/sync_all.ps1`。
- 不调用 xttrader。
- 不真实下单。
- 不查资金、持仓、订单、成交。
- 不真实发送通知。
- AI / Research / Model Lab / Agent 只能产出建议或 TradeIntent，不能直接下单。
- 所有交易必须经过 Risk Gate。

## 5. 数据路线

现阶段先用本地文件缓存而不直接上数据库，是为了保持部署简单、便于人工检查、降低依赖和损坏风险。`market_data/` 用于本地历史行情缓存，不提交 Git。DataHub 支持 cache hit / miss / warmup：命中则直接读取，缺失则通过 provider 补齐后写入缓存。未来可升级 SQLite / DuckDB / PostgreSQL。与 Qlib / vn.py 的关系是借鉴数据管理、回测流程和工程思路，不整体引入源码。

## 6. 后续阶段完整计划

- 阶段十六：ETF Universe 历史数据自动补全策略。
- 阶段十七：Research 使用真实/缓存历史数据。
- 阶段十八：ETF 策略从历史数据生成真实因子。
- 阶段十九：Daily Pipeline 接入真实缓存行情。
- 阶段二十：Human Approval 人工确认层。
- 阶段二十一：Paper Trading / QMT dry-run 适配。
- 阶段二十二：实盘前安全审计。
- 阶段二十三：小资金实盘灰度，但默认仍关闭。
- 阶段二十四：监控、告警、异常熔断。
- 阶段二十五：多策略组合和资金分配。
- 阶段二十六：Agent Research Layer。
- 阶段二十七：长期性能评估和回测归因。

## 7. 后续 Codex 开发规则

- 每个新阶段开始前，先阅读 `docs/qmt-ai-trading-project-roadmap.md`。
- 再阅读 `docs/qmt-ai-trading-architecture.md`。
- 再阅读对应上一阶段文档。
- 小修复优先本地脚本修，不要大改架构。
- 不要越级接实盘。
- 不要为了测试绕过风控。
- 不要引入重依赖。
- 不要整体引入 Qlib / vn.py / TradingAgents 源码。

## 8. 阶段十七进度：Research 使用缓存历史数据

阶段十七新增 Cached Research 数据源：Research 可以通过 `LocalBarStore` / `BarQuery` 只读本地 `market_data/` 历史 K 线，生成 `ResearchScore` 和 `ETFCandidate`，并接入 dry-run Daily Pipeline。缓存缺失或 bars 不足时返回 warning / 空结果，不下载数据、不调用 QMT、不调用 `xttrader`、不下单。

后续开发前仍必须先读本文档，再读 `docs/qmt-ai-trading-architecture.md`，再读对应上一阶段文档。
