# 阶段二十七：长期回测与绩效归因

## 阶段二十七目标

阶段二十七为 cached_real_first、Cached ETF Rotation 与 Portfolio Plan 的 dry-run 策略增加长期回测与绩效归因能力。系统只读取 `LocalBarStore` 本地历史 ETF bars，在多个 rebalance dates 上模拟候选生成、组合计划、dry-run TradeIntent、Risk Gate 校验和组合净值曲线。

## 为什么需要长期回测与绩效归因

单日 dry-run pipeline 只能说明当日信号是否可用，不能说明策略在多个周期中的收益、回撤、波动、换手、胜率、调仓频率和 Risk Gate 拦截影响。长期回测用于在不触达实盘的前提下评估策略稳定性，并把因子贡献、标的贡献和风控拦截拆开记录。

## LongPortfolioBacktestConfig

`LongPortfolioBacktestConfig` 包含 symbols、start_date、end_date、frequency、rebalance_frequency、cache_root、min_bars、lookback_bars、initial_cash、portfolio_method、portfolio_top_n、cash_reserve_ratio、max_symbol_weight、max_portfolio_weight、rebalance_threshold、data_source_mode、quality_report_dir、allow_unknown_quality_for_dry_run、risk_gate_enabled 和 metadata。

## LongBacktestResult

`LongBacktestResult` 记录 run_id、created_at、period、data_source、cache_quality、equity_curve、trades、summary、factor_attribution、warnings、success、message 和 metadata。模型只保存模拟回测信息，不保存真实账号、Token、密钥、真实资金或真实持仓。

## Performance summary 指标说明

- total_return：最终权益相对 initial_cash 的累计收益。
- annualized_return：按 252 个交易日近似年化。
- max_drawdown：最大回撤，使用非正比例表示，例如 `-0.10` 表示回撤 10%。
- volatility：日收益年化波动率。
- sharpe：基于日收益和无风险收益的简化 Sharpe。
- win_rate：正收益周期占比。
- turnover：允许通过 Risk Gate 的模拟成交额 / initial_cash。
- trade_count：允许通过 Risk Gate 的模拟交易数量。
- rebalance_count：调仓日期数量。
- risk_blocked_count：Risk Gate 拒绝的模拟 TradeIntent 数量。

## Factor attribution / Symbol attribution / Risk Gate attribution

Factor attribution 使用 score、momentum、volatility、volume 的入选候选平均暴露与近似贡献。Symbol attribution 汇总每个 symbol 的 allowed / blocked 数量和金额。Risk Gate attribution 单独统计 blocked_count、blocked_value 和 blocked_reasons。

## portfolio plan performance 与 risk-executable performance 的区别

Portfolio plan performance 表示组合层按目标权重生成的计划表现；risk-executable performance 只统计 Risk Gate `allowed=True` 的模拟交易表现。Risk Gate 拒绝的 intent 会记录在 trades 中，但不能计入 executable trades、turnover 或实际组合持仓变化。

## run_long_portfolio_backtest.py 使用方式

```powershell
py scripts/run_long_portfolio_backtest.py --cache-root market_data_test_stage27 --universe-name default_etf --start 2026-03-20 --end 2026-06-18 --frequency 1d --rebalance-frequency 5d --lookback-bars 20 --min-bars 20 --initial-cash 1000000 --portfolio-method score_weight --portfolio-top-n 2 --cash-reserve-ratio 0.2 --max-symbol-weight 0.2 --max-portfolio-weight 0.8 --output backtest_reports_stage27/long_backtest.md --json-output backtest_reports_stage27/long_backtest.json
```

## 安全边界

当前阶段仍不实盘、不调用 QMT 交易接口、不调用 `xttrader`、不下单、不查询真实资金/持仓/订单/成交。长期回测只读本地缓存，所有模拟 TradeIntent 仍要走 Risk Gate。

## 下一阶段计划

阶段二十八：异常监控、告警、熔断。目标是对数据缺失、缓存异常、信号异常、Risk Gate 连续拒绝、回测异常、调度失败等情况建立监控事件、告警等级和熔断规则。阶段二十八默认通知 dry-run，不真实发送邮件/Telegram/企业微信，不调用 `xttrader`、不真实下单。
