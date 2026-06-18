# 阶段十七：Cached Research 本地缓存研究数据源

后续开发应先阅读 `docs/qmt-ai-trading-project-roadmap.md`。

## 阶段十七目标

阶段十七让 Research / Model Lab / ETF 评分可以优先读取已经 warmup 的本地历史行情缓存，而不是只依赖手动传入 bars 或 mock 数据。当前阶段仍然只做 dry-run / shadow：不下载数据、不调用 QMT 交易接口、不调用 `xttrader`、不下单。

## 为什么 Research 要从缓存历史数据读取

阶段十五和阶段十六已经把历史行情缓存补全职责放在 warmup 流程中。Research 读取缓存可以：

- 复用 `market_data/` 中已经补齐的 ETF 历史 K 线；
- 避免 Research 在评分过程中临时访问 provider；
- 让因子计算、`ResearchScore`、`ETFCandidate` 和 Daily Pipeline 输入保持可复现；
- 在缓存缺失时返回 warning / 空结果，而不是中断 dry-run pipeline。

## CachedResearchRequest / CachedResearchDataset

`qmt_ai_trading/research/cache_reader.py` 新增三类只读数据结构：

- `CachedResearchRequest`：描述 symbols、日期区间、frequency、cache_root、min_bars、allow_partial 和 metadata。
- `CachedResearchItem`：描述单个 symbol 的读取结果、bar_count、bars、source、message 和 metadata。
- `CachedResearchDataset`：汇总多 symbol 读取结果，包括 success、total_symbols、loaded_symbols、failed_symbols 和 message。

读取函数内部使用 `LocalBarStore` / `BarQuery`，只查询本地缓存，不调用 provider 下载，也不调用任何交易接口。

## score_symbols_from_cache / score_etf_universe_from_cache

`qmt_ai_trading/research/cache_scoring.py` 提供：

- `score_symbols_from_cache(...)`：读取指定 symbols 的缓存 bars，并复用现有 Research 因子评分逻辑生成 `ResearchScore`。
- `score_etf_universe_from_cache(...)`：读取默认 `default_etf` universe 或显式 symbols，并生成缓存来源的 Research scores。
- `build_candidates_from_cached_research(...)`：把 cached research scores 转换为 `ETFCandidate`，并在 metrics 中标记 `source="cached_research"`。

缓存不足时，失败 symbol 会生成不可交易的 ResearchScore / candidate，pipeline 继续 dry-run。

## 与 Universe Warmup 的关系

Universe Warmup 仍然负责补齐历史数据：

1. `warmup_etf_universe.py` 检查并补齐 ETF universe 的本地缓存；
2. `run_cached_research.py` 只读取缓存并评分；
3. `run_daily_pipeline.py --use-cached-research` 把评分结果送入 ETF Strategy、TradeIntent、Risk Gate 和 Shadow Replay。

Research 不下载数据，数据缺口应回到 warmup 流程处理。

## 推荐运行顺序

```powershell
py scripts/warmup_etf_universe.py --lookback-days 10 --frequency 1d --provider mock --cache-root market_data_test_stage17
py scripts/run_cached_research.py --universe-name default_etf --start 2026-06-08 --end 2026-06-18 --frequency 1d --cache-root market_data_test_stage17 --min-bars 5
py scripts/run_daily_pipeline.py --use-cached-research --cache-root market_data_test_stage17 --research-start 2026-06-08 --research-end 2026-06-18 --research-frequency 1d --min-bars 5
```

## Scheduled pipeline 联合使用

可在 scheduled pipeline 中先 warmup universe，再使用 cached research：

```powershell
py scripts/run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 10 --warmup-frequency 1d --cache-root market_data_test_stage17 --use-cached-research --research-start 2026-06-08 --research-end 2026-06-18 --research-frequency 1d --min-bars 5
```

注册计划任务默认仍是 dry-run 预览，不传 `--execute` 不会真实注册：

```powershell
py scripts/register_daily_pipeline_task.py --warmup-universe --warmup-provider mock --universe-lookback-days 10 --warmup-frequency 1d --cache-root market_data --use-cached-research --research-start 2026-06-08 --research-end 2026-06-18 --research-frequency 1d --min-bars 5 --time 15:30
```

## 安全边界

当前阶段不下载、不调用 QMT、不调用 `xttrader`、不查询资金/持仓/订单/成交、不下单、不真实发送通知。`market_data/`、`data_cache/`、`market_data_test_stage17/`、`reports/`、`logs/` 仍然不提交 Git。

## 后续阶段

后续阶段可以在安全审计后，把 cached research 作为默认 pipeline 数据源，并继续保持 warmup、Research、Strategy、Risk Gate 与 Gateway 的边界。
