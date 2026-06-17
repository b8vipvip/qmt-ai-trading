# Stage 8: Backtest / Shadow Replay 标准化

## 职责

Stage 8 建立轻量级 Backtest / Shadow Replay baseline，用于在不连接真实 QMT、不下真实订单的前提下，对 Strategy / Research / Model Lab 产出的 `TradeIntent` 做历史回放、模拟成交、资产曲线和指标评价。

Backtest 层只处理：

- `TradeIntent`
- 模拟成交
- 模拟资产账户
- 结构化交易日志
- 结构化回测报告

真实交易仍必须经过 Risk Gate + QMT Gateway；Backtest / Shadow Replay 不允许绕过风控或直接调用真实下单接口。

## 输入

`run_simple_backtest` 和 `replay_trade_intents` 支持轻量输入：

- `list[TradeIntent]`
- price map，例如 `{ "510300.SH": 4.0 }`
- bars map，例如 `{ "510300.SH": [MarketBar(...)] }`

当同时提供 price map 和 bars 时，优先使用 price map；否则可使用 bar close 作为简单成交价格。

## 输出

Backtest 输出 `BacktestResult`，包含：

- initial / final cash
- final asset
- trades
- equity curve
- total return
- max drawdown
- win rate
- metrics / metadata

Shadow Replay 输出 `ShadowReplayResult`，包含：

- replay events
- 可选 backtest result
- report
- metadata

## 指标

当前阶段提供纯 Python 指标函数：

- `compute_total_return`
- `compute_max_drawdown`
- `compute_win_rate`
- `compute_equity_curve`
- `summarize_backtest_result`

空输入和数据不足时应返回稳定的结构化结果，不抛不可控异常。

## 当前限制

当前实现是轻量模拟，不是完整撮合引擎：

- 不模拟盘口深度
- 不模拟滑点队列
- 不做多账户、多币种、复杂公司行为
- 不整体引入 Qlib / vn.py / TradingAgents 源码
- 不依赖 pandas / numpy 作为硬要求

## 安全边界

Backtest / Shadow Replay：

- 不连接真实 QMT
- 不下单
- 不调用 `qmt_order.place_order`
- 不调用真实 `order_stock`
- 不读取敏感日志路径
- 不写入真实账号、Token、密钥、数据库

## 与 Strategy / Research / Model Lab 的关系

ETF Strategy、ResearchScore、ModelPrediction 可先转换为 dry-run `TradeIntent`，再进入 Backtest 验证。Stage 8 只提供验证闭环，不改变旧 ETF / DataHub / Risk / Gateway / Research / Model Lab 逻辑。

## 后续方向

后续可在不破坏安全边界的前提下：

- 对接现有 shadow replay / dry-run 日志 adapter
- 增加滑点、涨跌停、停牌等市场约束
- 增加更丰富的绩效指标
- 输出更完整的策略研究报告
