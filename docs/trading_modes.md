# QMT 三层验证边界

- `research_backtest`：快速研究，只验证策略想法，不作为实盘依据。
- `shadow_replay`：接近真实成交的历史回放，是 ETF 轮动策略验证主线，应纳入滑点、佣金、最小交易单位、现金占用、持仓均价、最大回撤、成交记录、风控拒绝记录、同日买卖限制和单日交易次数限制。
- `daily_dryrun`：真实账户只读计划，只读账户和行情，不下单；最终仓位和计划金额必须经过 Risk Engine。

`qmt_backtest_ma.py` 仅作为 MA 示例和流程验证，不作为实盘策略依据。

当前是否允许实盘：否。
当前是否允许小资金实盘：否。
原因：`live_trading_enabled=false`、daily dry-run 未满 20 个交易日、Risk Engine 尚未完全验收、仍存在年度回撤/过拟合/集中度风险。

## 旧版 QMT 直连脚本隔离

旧版 `qmt_plan_order_dryrun.py` / `qmt_plan_order_dryrun_test_buy.py` / `qmt_query_readonly.py` 已被统一 Gateway 架构替代。
如本地存在这些旧文件，更新脚本会自动移动到备份目录，不再参与运行和测试。
当前 dry-run 请使用 `qmt_plan_order_dryrun_v2.py`。
