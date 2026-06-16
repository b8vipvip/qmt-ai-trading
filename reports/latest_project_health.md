# 项目健康验收报告

- QMT连接是否正常：否（Codex环境需本地验证）
- Git是否干净：否
- 安全扫描是否通过：是
- 当前是否允许实盘：否
- 当前是否允许小资金实盘：否
- 原因：live_trading_enabled=false；daily dry-run 未满 20 个交易日；Risk Engine 尚未完全验收；仍存在年度回撤/过拟合/集中度风险
