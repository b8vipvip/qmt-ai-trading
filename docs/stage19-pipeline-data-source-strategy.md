# Stage 19: Pipeline Data Source Strategy

阶段十九为 Daily Pipeline 增加统一数据源决策层，让研究/策略输入在 dry-run / shadow 边界内根据配置与本地缓存覆盖率选择来源。

## 目标

- 先评估本地 `market_data/` cache coverage，再决定是否使用 cached research。
- 在显式允许时才 fallback 到 mock/default dry-run 数据。
- 在报告中输出 selected_source、cache hit/miss/fetched/skipped/failed、coverage、confidence、fallback 与是否允许生成 TradeIntent。
- 数据源切换只影响研究/策略输入；不改变 Risk Gate、dry-run、shadow 等安全边界。

## 为什么需要数据源决策层

阶段十七和阶段十八已经能从缓存历史因子生成 ETF 信号。阶段十九把“是否使用缓存、缓存是否足够、是否允许 fallback”的判断集中到 `qmt_ai_trading.pipeline.data_source`，避免 Daily Pipeline、脚本和计划任务各自隐式选择数据源。

## data_source_mode

- `legacy`：保持旧 dry-run 行为，使用 DataHub 默认 ETF universe / mock score 生成候选。
- `cached`：强制使用本地缓存 cached research + cached ETF rotation；缓存不足时不 fallback，且 `allow_trade_intents=False`。
- `auto`：优先使用 cached research；缓存不足时只有传入 `--allow-mock-fallback` 才 fallback 到 mock。
- `mock`：显式使用旧 mock/default dry-run 行为，并标记低可信度。

## Cache coverage

`coverage_ratio = loaded_symbols / total_symbols`。一个 symbol 只有在本地缓存命中且 bars 数量达到 `min_bars` 时才计入 loaded/hit。

## Confidence

- `HIGH`：使用 `cached_research`，coverage 达到阈值，且 loaded symbols 达到最低要求。
- `MEDIUM`：部分缓存可读但不足以满足全部阈值。
- `LOW`：mock/fallback 或数据不足。

## Fallback/mock 风险提示

`mock/fallback data is for dry-run validation only and should not be used for live trading decisions.`

Fallback/mock 仅用于验证 pipeline 结构，不可作为真实交易依据。

## check_pipeline_data_source.py

```bash
py scripts/check_pipeline_data_source.py --data-source-mode cached --cache-root market_data_test_stage19 --start 2026-05-09 --end 2026-06-18 --frequency 1d --min-bars 20
py scripts/check_pipeline_data_source.py --data-source-mode auto --allow-mock-fallback --cache-root market_data_missing_stage19 --start 2026-05-09 --end 2026-06-18 --frequency 1d
```

该脚本只检查数据源决策，不下载数据、不调用 QMT、不调用 `xttrader`、不下单。

## run_daily_pipeline.py

```bash
py scripts/run_daily_pipeline.py --data-source-mode cached --cache-root market_data_test_stage19 --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 1
py scripts/run_daily_pipeline.py --data-source-mode auto --allow-mock-fallback --cache-root market_data_missing_stage19 --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20
```

## Scheduled pipeline 推荐参数

后续计划任务建议使用：

```bash
--warmup-universe --data-source-mode cached
```

阶段十九当前不下载、不调用 QMT、不调用 `xttrader`、不下单。后续阶段可以在缓存 warmup 稳定后，将 `cached` 模式作为默认 dry-run pipeline。
