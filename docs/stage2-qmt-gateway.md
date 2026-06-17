# 阶段二：QMT Gateway 标准化

## QMT Gateway 的职责

QMT Gateway 是项目内唯一面向 QMT 交易执行能力的标准适配层，负责接收已经结构化的 `TradeIntent`，调用 Risk Gate 完成实盘前校验，并返回统一的 `OrderResult`。Gateway 不做策略判断、不做 AI 分析，也不允许 Agent、Strategy 或 Research 绕过 Risk Gate 直接触达下单能力。

## 标准流程

```text
TradeIntent -> Risk Gate -> qmt_order.place_order -> OrderResult
```

`TradeIntent` 必须先经过 `validate_trade_intent`。只有 Risk Gate 返回允许后，`qmt_order.place_order` 才能继续处理；如果 Risk Gate 拒绝，Gateway 必须返回失败的 `OrderResult` 和明确原因。

## 安全默认值

- 导入 QMT Gateway 模块时不连接 QMT，不读取账户，不提交委托。
- `dry-run` 默认开启，用于模拟和流程验证。
- 实盘交易默认关闭，`LIVE_TRADING_ENABLED=False` 时所有非 dry-run 委托都必须拒绝。
- 当前 `qmt_order` 仍然是安全占位，不直接调用真实 `order_stock`。

## 后续真实 QMT 下单接入要求

后续如需接入真实 QMT 下单，必须显式新增并审查真实适配器，继续通过 Risk Gate，继续保留人工确认和实盘开关，不允许在 Strategy、Agent、Research 或 UI 中直接调用真实下单函数。
