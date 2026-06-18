# Daily Pipeline 运行手册

## Warmup
`py scripts/warmup_etf_universe.py --provider mock --cache-root market_data_test_stage32 --lookback-days 40 --frequency 1d`

## Daily Pipeline
`py scripts/run_daily_pipeline.py --data-source-mode cached_real_first --cache-root market_data_test_stage32 --allow-mock-fallback --use-cached-research --enable-portfolio-plan --enable-monitoring --enable-agent-research --agent-research-mode local_rules --enable-live-gray-readiness --build-dashboard`

## 参数说明
- `cached_real_first`：优先本地缓存和质量证据；不足时仅在显式 `--allow-mock-fallback` 下使用 mock fallback。
- cache quality `UNKNOWN`：代表缺少正式质量证据，仅适合 dry-run / shadow。
- portfolio 参数：`--enable-portfolio-plan`、`--portfolio-top-n`、资金和权重上限。
- monitoring 参数：`--enable-monitoring`、`--monitoring-dry-run-alerts`。
- agent 参数：`--enable-agent-research --agent-research-mode local_rules`。
- live gray 参数：`--enable-live-gray-readiness`，不传 `--live-enabled`。
- dashboard 参数：`--build-dashboard --dashboard-output dashboard_stage32/daily_dashboard.html`。

当前阶段仍不实盘、不调用 QMT 交易接口、不调用 xttrader、不查询真实资金/持仓/订单/成交、不真实发送通知、不自动 approve、不自动 paper submit、不自动 live submit、不真实下单。
