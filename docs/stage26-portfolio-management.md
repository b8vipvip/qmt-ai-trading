# 阶段二十六：组合与资金管理层

## 阶段目标

阶段二十六在 cached ETF rotation / Daily Pipeline 生成单一或 top_n 信号之后，增加组合级资金管理、权重分配、现金保留、仓位上限、调仓阈值和本地持仓计划。该阶段只生成 dry-run / paper `PortfolioPlan`，不等于真实账户指令。

## 为什么需要组合与资金管理层

单一 ETF top_n 信号只能说明候选标的和方向，不能表达组合层约束。组合层用于在 Strategy / Cached ETF Rotation 之后、TradeIntent / Risk Gate 之前，把候选列表转换为目标权重、调仓计划和仍需风控校验的 dry-run TradeIntent。

## 核心模型

- `PortfolioSnapshot`：本地 mock/snapshot 当前持仓与现金输入；不查询真实 QMT 资金或持仓。
- `PortfolioTarget`：目标标的、目标权重、目标市值、score 与原因。
- `PortfolioAdjustment`：当前权重到目标权重的差异、BUY/SELL/HOLD、100 股整数倍数量与跳过原因。
- `PortfolioPlan`：一次组合计划，包含 targets、adjustments、dry-run trade_intents、warnings 和安全元数据。

## 权重方法

- `equal_weight`：对入选 candidates 平均分配。
- `score_weight`：按 score 正比例倾斜分配。
- `risk_adjusted_weight`：按 score 并结合 volatility 惩罚进行分配。

## 组合约束

- `cash_reserve_ratio`：现金保留比例，限制最大可投资权重。
- `max_symbol_weight`：单标的最大权重。
- `max_portfolio_weight`：组合最大总权重。
- `rebalance_threshold`：小于阈值的权重差异跳过，避免频繁微调。

## run_portfolio_plan.py 使用方式

```powershell
py scripts/run_portfolio_plan.py --cache-root market_data_test_stage26 --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --method score_weight --top-n 2 --total-asset 1000000 --cash-reserve-ratio 0.2 --max-symbol-weight 0.3 --max-portfolio-weight 0.8 --output portfolio_test_stage26/portfolio_plan.md --json-output portfolio_test_stage26/portfolio_plan.json
```

该脚本只读本地缓存和 cached research，不调用 QMT、不调用 `xttrader`、不下单。

## run_daily_pipeline.py --enable-portfolio-plan 使用方式

```powershell
py scripts/run_daily_pipeline.py --cache-root market_data_test_stage26 --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 2 --enable-portfolio-plan --portfolio-method score_weight --portfolio-top-n 2 --portfolio-total-asset 1000000 --portfolio-cash-reserve-ratio 0.2 --portfolio-max-symbol-weight 0.3 --portfolio-max-weight 0.8
```

默认不开启 portfolio plan；开启后报告展示 Portfolio Plan 区块，Portfolio 生成的 TradeIntent 仍走 Risk Gate。

## scheduled pipeline portfolio 参数

`run_scheduled_daily_pipeline.py` 和 `register_daily_pipeline_task.py` 透传 `--enable-portfolio-plan`、`--portfolio-method`、`--portfolio-top-n`、`--portfolio-cash-reserve-ratio`、`--portfolio-max-symbol-weight`、`--portfolio-max-weight`、`--portfolio-rebalance-threshold`、`--portfolio-total-asset`、`--portfolio-current-cash`、`--portfolio-snapshot-path`。

## 安全说明

Portfolio plan is dry-run/paper only and is not an order instruction.

当前阶段仍不实盘、不调用 QMT 交易接口、不调用 `xttrader`、不下单、不查询真实资金/持仓/订单/成交。Portfolio 不等于真实账户，当前持仓只允许本地 mock/snapshot 输入。

## 下一阶段

阶段二十七：长期回测与绩效归因。目标是对 `cached_real_first + portfolio plan` 的 dry-run 策略进行多周期回测，输出收益、回撤、换手、胜率、调仓次数、因子贡献和组合归因报告。阶段二十七仍不实盘、不调用 `xttrader`、不真实下单。
