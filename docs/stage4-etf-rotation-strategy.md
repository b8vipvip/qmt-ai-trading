# 阶段四：ETF Rotation Strategy Engine 标准化

## 定位与职责

ETF Rotation Strategy Engine 位于 Research / Agent 输出与 Risk Gate 之间，职责是把 ETF 候选池、评分和仓位意图整理为标准化 `TradeIntent`。策略层只做信号生成，不做账户读取、不连接 QMT、不直接下单。

## 输入

阶段四标准策略入口接收已经准备好的 ETF 候选数据，包括但不限于：

- ETF 代码、名称与候选池来源；
- 价格字段，例如 `last_price` / `last_close`；
- 动量与趋势字段，例如 5 日、20 日、60 日收益率、均线趋势；
- 波动率、最大回撤、成交额 / 流动性等风控评分数据；
- 已有 `data_tools.etf_rotation_selector` 产生的 `score`、`eligible`、`skip_reason` 等评分结果。

现有 `data_tools/etf_rotation_selector.py` 仍保留为只读研究评分实现。阶段四通过映射字段或 adapter 复用其输出，不为了标准策略接口重写全部历史评分逻辑。

## 输出

策略输出仅允许为：

- 单个 `TradeIntent`；或
- `list[TradeIntent]`。

当没有 ETF 候选或没有候选通过筛选时，策略返回 `HOLD` intent 或空 intents，并在 `reason` 中说明没有候选 / 没有合格候选。

## 安全边界

- 不直接下单；
- 不调用真实 QMT `order_stock`；
- 不调用 `qmt_order.place_order`；
- 默认 `dry_run=True`；
- 默认 `source="etf_rotation"`；
- BUY 数量按 100 股整数倍生成；
- `target_percent` 不超过环境变量 `MAX_POSITION_PCT` 对应的最大单票仓位；
- 所有真实下单仍必须经过 `TradeIntent -> Risk Gate -> QMT Gateway` 标准流程。

## 后续接 Research 层和 Agent 层

后续 Research 层可以继续负责 ETF universe、行情下载、因子计算、评分、回测与 shadow replay，并把结果以 `ETFCandidate` 或兼容字典形式交给 Strategy Engine。Agent 层只负责解释、风险提示和结构化建议，不直接生成或执行 QMT 订单。

## 后续接 QMT 实盘确认

当策略输出 `TradeIntent` 后，应先调用 Risk Gate 完成结构校验、黑名单、仓位上限、100 股整数倍和实盘开关等检查。只有 Risk Gate 允许且人工确认、实盘开关、QMT Gateway 真实适配器均显式开启后，才允许进入实盘执行路径。阶段四不改变当前实盘默认关闭的安全策略。
