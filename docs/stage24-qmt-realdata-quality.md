# 阶段二十四：QMT 实机数据联调与真实缓存质量验证

## 阶段二十四目标

阶段二十四只做真实 MiniQMT / `xtquant.xtdata` 历史行情小范围联调和本地缓存质量验证。默认样本为 `510300.SH`、`1d`、`2024-01-01` 到 `2024-01-10`，缓存写入 `market_data_qmt_stage24/`，质量报告写入 `qmt_data_quality_reports/`。

## 为什么要做 QMT 实机数据联调

阶段十三和阶段十四已经建立 QMT historical provider 与字段校准能力；阶段二十四进一步验证真实 `xtdata` 行情能否被小范围拉取、归一化、保存到 `LocalBarStore`，并在保存后重新读取确认 cache hit。

## 为什么本阶段仍不交易

本阶段产物仅证明行情读取和缓存质量，不构成交易授权。系统仍处于实盘前验证阶段，不查询资金、持仓、订单、成交，不提交真实订单。

## xtdata 与 xttrader 的边界

- 允许：延迟导入并使用 `xtquant.xtdata` 的历史行情读取能力。
- 禁止：导入 `xtquant.xttrader`，调用 order / trade / buy / sell / cancel / asset / position 等交易相关接口。

## qmt_realdata_smoke_test.py 使用方式

```powershell
py scripts/qmt_realdata_smoke_test.py --symbol 510300.SH --start 2024-01-01 --end 2024-01-10 --frequency 1d --cache-root market_data_qmt_stage24 --report-dir qmt_data_quality_reports --write-json
```

脚本会先执行 runtime diagnostics；如果 `xtdata` 不可用，输出 `UNAVAILABLE` 并生成可读报告，默认返回码为 0；如果可用，则用 `QmtHistoricalDataProvider` 拉取小范围 K 线，保存到 `LocalBarStore`，再读取验证 cache roundtrip。

## check_qmt_cache_quality.py 使用方式

```powershell
py scripts/check_qmt_cache_quality.py --symbols 510300.SH,510500.SH --start 2024-01-01 --end 2024-01-10 --frequency 1d --cache-root market_data_qmt_stage24 --report-dir qmt_data_quality_reports --write-json --min-bars 1
```

该脚本只读本地缓存，不调用 QMT，不导入 `xtdata`，不导入 `xttrader`。

## QmtDataQualityReport 字段说明

报告包含 report_id、created_at、symbol、frequency、start_date、end_date、provider、xtdata_available、qmt_available、cache_root、raw_row_count、normalized_bar_count、cache_hit_after_save、first_datetime、last_datetime、duplicate_datetime_count、missing_ohlc_count、zero_volume_count、sorted_by_datetime、checks、decision、message 和 metadata。

## QmtRealDataPlan 小范围限制说明

`QmtRealDataPlan` 默认 `max_symbols=5`、`max_days=90`。超过限制时返回 WARN；strict 模式可升级为 FAIL，用于防止误拉大规模真实行情数据。

## 无 xtquant 环境下的预期行为

无 MiniQMT / `xtquant` 时，smoke test 输出 `UNAVAILABLE` / `SKIPPED`，写 Markdown / JSON 报告，并提示切换到 MiniQMT Python 环境重试；默认不让测试崩溃。

## 真实 MiniQMT 环境下的预期行为

真实环境中应启动 MiniQMT，使用能导入 `xtquant.xtdata` 的 Python 解释器运行 smoke test。脚本拉取小范围 ETF 历史 K 线、字段归一化、保存缓存、重新读取并生成质量报告。

## 质量检查项

- 字段完整性：open / high / low / close 不应缺失。
- 日期范围：报告记录 first_datetime / last_datetime。
- 重复日期：duplicate_datetime_count 应为 0。
- 缺失 OHLC：missing_ohlc_count 应为 0。
- 零成交量：zero_volume_count 会触发 WARN。
- 排序：sorted_by_datetime 应为 True。
- cache roundtrip：保存后读取应 cache_hit_after_save=True。

## 当前阶段安全边界

当前阶段不调用 QMT 交易接口、不调用 `xttrader`、不实盘、不下单、不查询资金/持仓/订单/成交、不发送真实通知。

## 下一阶段计划

阶段二十五：Daily Pipeline 真实缓存数据默认化。阶段二十五将在阶段二十四真实缓存质量验证通过后，把 Daily Pipeline 默认数据源逐步切换为 cached_real_data 优先；mock fallback 必须显式开启，并在报告中展示真实缓存覆盖率、数据质量等级和信号可信度。阶段二十五仍不实盘、不调用 `xttrader`、不真实下单。
