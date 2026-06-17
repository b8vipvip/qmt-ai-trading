# 阶段一：项目安全和结构基线

## 阶段一目标

阶段一只建立安全边界和标准目录结构，继续保护当前已经跑通的国金证券 QMT 接口与基础逻辑。此阶段不接入 TradingAgents、Qlib、vn.py 的实际复杂代码，不做 UI，不重构现有 QMT 执行链路。

## 新增目录说明

- `qmt_ai_trading/gateway/`：后续封装 QMT 行情、账户、委托等适配层。
- `qmt_ai_trading/datahub/`：后续统一证券代码、行情和外部数据源入口。
- `qmt_ai_trading/research/`：后续承载因子、模型、回测评价等研究能力。
- `qmt_ai_trading/agents/`：后续承载分析型 Agent，只输出结构化建议。
- `qmt_ai_trading/strategies/`：后续承接数据、研究和 Agent 输出，生成 `TradeIntent`。
- `qmt_ai_trading/risk/`：所有实盘前校验与拦截的 Risk Gate。
- `qmt_ai_trading/config/`：运行配置入口，只从环境变量读取敏感配置。
- `qmt_ai_trading/common/`：跨层共享的基础类型定义。
- `tests/`：测试目录，保留现有测试并为后续模块补充用例。

## 默认 dry-run

系统配置默认 `DRY_RUN=True`。策略示例、Agent 示例和 Gateway 空壳都不得直接触发实盘下单。阶段一的示例信号只用于结构验证和模拟流程。

## 实盘默认关闭

系统配置默认 `LIVE_TRADING_ENABLED=False`。当该配置没有显式开启时，实盘委托必须被拒绝或只返回 dry-run 结果。任何模块都不得绕过 Risk Gate 调用 QMT 实盘下单。

## 后续如何接 TradingAgents / Qlib / vn.py

- TradingAgents：只借鉴多 Agent 投研流程，输出结构化 `AgentDecision`，不复制 UI，不允许 Agent 直接下单。
- Qlib：只借鉴因子工程、数据集构建、模型训练和评价思想，必要时作为独立依赖或离线研究工具接入。
- vn.py / vnpy.alpha：只参考因子、事件驱动、风控和适配器设计，必要时抽取少量思想或通过 adapter 对接。

## 第三方项目接入边界

第三方项目不整体搬入本仓库，不把 TradingAgents-CN 的 `app/` 和 `frontend/` 复制进来，不把 Qlib 或 vn.py 整个项目复制进来。后续只提取核心思想、少量必要模块，或以依赖和 adapter 方式接入，并保持本项目作为主系统。
