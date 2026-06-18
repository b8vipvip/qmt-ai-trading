# 阶段十八：Cached ETF Rotation

## 目标

阶段十八把 Stage 17 Cached Research 从本地缓存读取到的历史行情因子正式接入 ETF Rotation。缓存数据足够时，Daily Pipeline 可以基于 cached factor score 生成 dry-run `TradeIntent`；缓存不足时继续安全输出 no eligible candidates。

## Cached Research 与 ETF Rotation 的关系

- `Cached Research` 只读 `LocalBarStore` 本地缓存，不下载数据。
- `cache_scoring.py` 计算 momentum、volatility、volume factor，并输出 `ResearchScore`。
- `cached_etf_rotation.py` 将 `ResearchScore` 标准化为 `ETFCandidate`，按 factor score 过滤、排序、选 top N，再生成 dry-run `TradeIntent`。
- 所有意图仍进入 Daily Pipeline 的 Risk Gate 校验。

## CachedETFSignalConfig / CachedETFSignalResult

`CachedETFSignalConfig` 控制 top_n、max_position_pct、min_score、min_bars、momentum/volatility/volume 权重、低波动偏好和 metadata。

`CachedETFSignalResult` 输出 candidates、selected_candidates、trade_intents、skipped_symbols、message 和 metadata，便于 pipeline/report 展示。

## 数据足够与不足行为

- 数据足够：`bar_count >= min_bars` 且 factor score 可计算，candidate eligible，reason 包含 cached factor score。
- 数据不足：candidate 不 eligible，进入 skipped_symbols，reason 说明缺少 bars 或窗口不满足；不强行交易。

## Factor score 如何影响 ETF 选择

默认使用 cached research 的综合 score，并结合 metadata 里的 momentum、volatility、volume_factor。默认偏好低波动，volatility 作为惩罚/反向加分项；最终按 score 降序选择 top N。

## run_cached_etf_signal.py

```powershell
py scripts/run_cached_etf_signal.py --universe-name default_etf --start 2026-05-01 --end 2026-06-18 --frequency 1d --cache-root market_data_test_stage18 --min-bars 20 --top-n 1
```

该脚本只读本地缓存，输出 loaded symbols、eligible candidates、skipped symbols、selected candidates 和 generated TradeIntent，不调用 QMT/xttrader，不下单。

## run_daily_pipeline.py cached ETF 参数

```powershell
py scripts/run_daily_pipeline.py --use-cached-research --cache-root market_data_test_stage18 --research-start 2026-05-01 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 1 --cached-strategy-min-bars 20
```

新增参数：

- `--cached-strategy-top-n`：cached ETF rotation 选择数量。
- `--cached-strategy-min-score`：cached ETF rotation 最低分。
- `--cached-strategy-min-bars`：策略层再次校验的最少 bars。

## Scheduled Pipeline 流程

推荐流程：

1. `--warmup-universe` 用 mock/qmt historical provider 补缓存。
2. `--use-cached-research` 从缓存读 bars 并计算 factor score。
3. `cached_etf_rotation` 生成 dry-run TradeIntent。
4. Risk Gate 校验。
5. Daily Pipeline 输出报告。

示例：

```powershell
py scripts/run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data_test_stage18 --use-cached-research --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 1 --cached-strategy-min-bars 20
```

## 安全边界

当前阶段不下载数据、不调用 QMT、不调用 xttrader、不下单。历史数据补全仍由 warmup 脚本或 Scheduler warmup 负责，Cached Research 和 Strategy 只读缓存并生成 dry-run 意图。

## 后续

后续阶段可以把 cached ETF rotation 作为默认 dry-run pipeline，同时继续保持 Human Approval、Risk Gate 和 QMT Gateway 边界。
