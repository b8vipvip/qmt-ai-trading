# 阶段二十五：Daily Pipeline 真实缓存数据默认化

## 目标

把 Daily Pipeline 默认数据源切到 `cached_real_first`：优先使用本地缓存行情和阶段二十四 QMT quality report 作为研究/策略输入证据。该阶段不是实盘授权，不调用 QMT 交易接口。

## 为什么切换到 cached real data first

阶段十九已经建立数据源决策，阶段二十四已经建立真实缓存质量报告。阶段二十五把两者合并，使 Daily Pipeline 默认不再静默使用 legacy/mock，而是先检查缓存覆盖率和质量证据。

## 模式与来源

- `cached_real_first`：pipeline 模式，先 cache coverage，再 quality gate。
- `cached_real_data`：PASS quality report 且覆盖满足阈值。
- `cached_unknown_quality`：缓存足够但缺少报告，仅 dry-run，质量 UNKNOWN。
- `cached_mock_data`：显式允许的 mock cache，LOW confidence。
- `mock_fallback`：显式 fallback，LOW confidence，不适合实盘决策。

## CacheQualityGatePolicy / CacheQualityGateDecision

`CacheQualityGatePolicy` 定义 require_quality_report、min_quality_level、allow_unknown_quality_for_dry_run、allow_mock_cache、stale report、coverage 阈值等策略。

`CacheQualityGateDecision` 输出 allowed、quality_level、selected_cache_type、quality_report_path、quality_report_decision、coverage_ratio、fallback_used、allow_trade_intents、message 和 remediation。

## 无 quality report 的行为

若 `require_quality_report=True`，缺报告会 blocked。若 `allow_unknown_quality_for_dry_run=True`，缺报告可 dry-run，但 quality 必须是 UNKNOWN，不能标记 HIGH。

## 有 PASS quality report 的行为

当 report decision 为 PASS 且 coverage 满足阈值时，质量为 HIGH，selected_source 为 `cached_real_data`。报告仍提示 dry-run/shadow 输出不是订单指令。

## fallback/mock 必须显式开启

缓存缺失时默认不生成 TradeIntent。只有显式传入 `--allow-mock-fallback`（以及需要允许 mock cache 时的 `--allow-mock-cache`）才会走 mock/fallback，并在报告中标记 LOW confidence 和不适合实盘决策。

## run_daily_pipeline.py 默认参数

`run_daily_pipeline.py` 默认 `--data-source-mode cached_real_first`、`--quality-report-dir qmt_data_quality_reports`、`--allow-unknown-quality-for-dry-run`、`--min-quality-level UNKNOWN`，默认 dry-run、不下单。

## check_cache_quality_gate.py

```powershell
py scripts/check_cache_quality_gate.py --cache-root market_data_test_stage25 --quality-report-dir qmt_data_quality_reports --start 2026-05-09 --end 2026-06-18 --frequency 1d --min-bars 20
```

该脚本只检查 cache coverage 与 quality gate，不调用 QMT、不调用 xttrader、不下单。

## scheduled pipeline 推荐参数

推荐使用：

```powershell
py scripts/run_scheduled_daily_pipeline.py --warmup-universe --data-source-mode cached_real_first
```

## 安全边界

阶段二十五仍不实盘、不调用 QMT 交易接口、不调用 `xttrader`、不下单、不查询资金/持仓/订单/成交。所有 TradeIntent 仍必须经过 Risk Gate，进入 paper 仍必须 Human Approval。

## 下一阶段

阶段二十六：组合与资金管理层。目标是增加组合级权重、最大仓位、现金保留、调仓阈值、持仓计划和组合风险约束，仍 dry-run / paper。
