# 阶段三十三：真实 QMT 数据质量长期追踪

## 阶段三十三目标
阶段三十三建立真实 QMT historical cache quality report 的长期追踪层，生成 Data Quality Ledger、Trend Report、Incident Report 与 DataQualityTrackingReport。

## 为什么需要真实 QMT 数据质量长期追踪
阶段二十四/二十五已经具备真实历史行情质量验证和 cached_real_first 入口；长期追踪用于跨日期观察 ETF universe 缓存覆盖率、缺失 bars、重复日期、价格/成交量异常和字段缺失趋势。

## 核心模型
- `DataQualityLedgerEntry`：单个 symbol/trade_date 的只读质量台账。
- `DataQualityTrend`：跨日期统计 PASS/WARN/FAIL/UNKNOWN/UNAVAILABLE、平均覆盖率和恶化趋势。
- `DataQualityIncident`：覆盖率过低、缺失 bars、重复 bars、异常和 unavailable 事件。
- `DataQualityTrackingReport`：汇总 ledger、trends、incidents、summary 和 safety note。

## run_data_quality_tracking.py 使用方式
```powershell
py scripts/run_data_quality_tracking.py --report-dir qmt_data_quality_reports --cache-root market_data_test_stage33 --symbols 510300.SH,510500.SH --start 2026-05-09 --end 2026-06-18 --output data_quality_tracking_stage33/data_quality_tracking.md --json-output data_quality_tracking_stage33/data_quality_tracking.json
```

## run_daily_pipeline.py --enable-data-quality-tracking 使用方式
```powershell
py scripts/run_daily_pipeline.py --enable-data-quality-tracking --data-quality-tracking-output-dir data_quality_tracking_stage33 --data-quality-tracking-report-dir qmt_data_quality_reports --data-quality-tracking-cache-root market_data_test_stage33 --data-quality-tracking-symbols 510300.SH,510500.SH --data-quality-tracking-start 2026-05-09 --data-quality-tracking-end 2026-06-18
```

## scheduled pipeline data quality tracking 参数说明
`run_scheduled_daily_pipeline.py` 和 `register_daily_pipeline_task.py` 支持 `--enable-data-quality-tracking`、`--data-quality-tracking-output-dir`、`--data-quality-tracking-report-dir`、`--data-quality-tracking-cache-root`、`--data-quality-tracking-symbols`、`--data-quality-tracking-start`、`--data-quality-tracking-end`。

## Monitoring / Dashboard 接入说明
Monitoring 通过 `detect_data_quality_tracking_events(report, config)` 将 ERROR/CRITICAL incident、FAIL trend 和覆盖率低于阈值转换为只读 MonitoringEvent。Dashboard 通过 Data Quality Tracking section 读取最新 Markdown/JSON 文件并展示，文件缺失时返回 EMPTY。

## 安全边界
当前阶段只读，不查询账户/资金/持仓/订单/成交；不调用 QMT 交易接口、不调用 xttrader、不真实发送通知、不下单。

## 下一阶段计划
阶段三十四：真实通知 dry-run 接入准备。阶段三十四默认不真实发送通知，不读取真实 token，不调用外部网络，只有在后续单独人工确认阶段才允许真实通知接入。
