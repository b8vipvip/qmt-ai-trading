# 阶段二：QMT Gateway 标准化

## 目标

阶段二把项目中已经跑通的 QMT / xtdata / xttrader 相关能力逐步封装到 `qmt_ai_trading/gateway/`，形成稳定的行情、账户、委托和连接管理边界。阶段二只新增 adapter / wrapper，不删除、不重命名、不破坏原有已经跑通的 QMT 脚本和入口。

## 安全原则

- **不在 import 时连接 QMT**：`qmt_market.py`、`qmt_account.py`、`qmt_client.py` 只在显式调用函数时创建或调用现有 adapter。
- **下单必须经过 Risk Gate**：标准下单入口 `place_order(intent)` 必须先调用 `validate_trade_intent(intent)`，策略和 Agent 不允许绕过该入口直接下单。
- **dry-run 默认开启**：`TradeIntent.dry_run=True` 时只返回模拟 `OrderResult`，不会调用真实 QMT 交易接口。
- **实盘默认关闭**：`LIVE_TRADING_ENABLED` 默认是 `False`；未显式开启时，`dry_run=False` 的委托必须被拒绝。
- **实盘 adapter 暂不接真实下单**：即使风险校验通过且显式开启实盘，阶段二仍只保留 TODO 占位，避免贸然接入真实委托接口。
- **不提交真实敏感信息**：账号、userdata 路径、Token、密钥均只能来自环境变量或本地未跟踪配置，不写入仓库。

## 标准模块

- `qmt_ai_trading/gateway/qmt_order.py`
  - `place_order(intent)`：阶段二标准委托入口。
  - `QmtOrderGateway.submit_order(intent)`：兼容对象封装。
- `qmt_ai_trading/gateway/qmt_market.py`
  - `get_latest_price(symbol)`：读取最新行情的标准函数壳。
  - `get_bars(symbol, period="1d", count=100)`：读取 K 线的标准函数壳。
- `qmt_ai_trading/gateway/qmt_account.py`
  - `get_account_asset()`、`get_positions()`、`get_orders()`、`get_trades()`：只读账户查询函数壳。
- `qmt_ai_trading/gateway/qmt_client.py`
  - `QmtClientManager`：读取 `qmt_account_id` 和 `qmt_userdata_path` 的连接管理占位，连接必须由显式函数触发。
- `qmt_ai_trading/gateway/models.py`
  - 轻量 dataclass 和转换函数，用于后续统一 asset / position / order / trade 数据结构。

## 与原有 QMT 代码的兼容方式

现有根目录脚本、`qmt_gateway/` 只读 adapter、研究和 dry-run 流程继续保留。阶段二新增的 `qmt_ai_trading/gateway/` 标准入口会优先以 adapter 方式调用现有只读逻辑；路径不清晰或涉及真实交易的部分只保留 TODO 和安全占位。

## 后续迁移建议

1. 先把只读行情脚本中稳定的 xtdata 调用迁移到 `qmt_market.py` 的 adapter 后面。
2. 再把只读账户查询统一到 `qmt_account.py`，并用 `models.py` 规范输出字段。
3. 最后才评审实盘委托 adapter；接入前必须补齐更完整的 Risk Gate、人工确认、审计日志和小资金开关。
4. 每迁移一个旧入口，都保留兼容导入或旧脚本 wrapper，避免破坏本地 MiniQMT 已跑通流程。
