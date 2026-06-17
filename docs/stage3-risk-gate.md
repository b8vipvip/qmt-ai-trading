# 阶段三：Risk Gate 完整化

## 定位

Risk Gate 是实盘前最后一道门。Agent、Strategy、Research 和任何后续 UI 都不能绕过 Risk Gate，也不能直接调用 QMT 实盘下单接口。

## 当前风控规则

- `side` 只允许 `BUY` / `SELL` / `HOLD`。
- `symbol` 不能为空。
- `quantity` 不能小于 0。
- `target_percent` 不能小于 0。
- A 股 `BUY` 数量必须是 100 股整数倍。
- `HOLD` 可以使用 `quantity=0`。
- `SELL` 不要求 100 股整数倍，但数量不能为负。
- 黑名单 `SYMBOL_BLACKLIST` 中的证券代码拒绝。
- 单票最大仓位由 `MAX_POSITION_PCT` 控制，默认 20%。
- `target_percent` 超过最大单票仓位时拒绝。
- `dry-run=True` 可以继续模拟，但仍必须通过基础规则。
- `dry-run=False` 且 `LIVE_TRADING_ENABLED=False` 时拒绝。
- `dry-run=False` 且实盘开关开启时，仍必须通过 `live_gate`。
- 默认 `REQUIRE_LIVE_CONFIRM=True`，人工确认开关未关闭或确认 token 为空时实盘拒绝。
- `risk_level` 使用 `LOW` / `MEDIUM` / `HIGH` 表达风险等级。

## 当前阶段边界

当前阶段不连接实时行情，不读取真实账户，不读取真实持仓，不做真实 ST、停牌、涨跌停判断。相关规则只保留 TODO 和后续接入点。

## 后续阶段

后续阶段再显式接入 QMT 行情、持仓、账户数据，用快照参数或受控适配器完善 ST、停牌、涨跌停、T+1、资金、持仓和组合级风险检查。实盘默认继续关闭，dry-run 默认继续开启。
