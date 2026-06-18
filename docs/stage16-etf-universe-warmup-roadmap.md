# 阶段十六：ETF Universe 历史数据自动补全策略

后续开发应先阅读 `docs/qmt-ai-trading-project-roadmap.md`。

## 阶段十六目标

阶段十六把阶段十五的手动 symbols warmup 扩展为 ETF Universe 自动补全，并新增项目总路线文档，确保后续方向不越界。

## ETF Universe 自动补全逻辑

`qmt_ai_trading/datahub/universe_warmup.py` 先解析 universe：默认 `default_etf` 调用 DataHub 内置 ETF universe；显式 `symbols` 优先于 universe。随后构造 stage 15 `CacheWarmupRequest`，逐个 symbol 调用历史行情缓存补全。

## 日期范围

- `--start` / `--end`：显式区间。
- `--lookback-days N`：以 end/today 往前 N 天。
- `--lookback-years N`：以 end/today 往前约 N * 365 天。
- `--end` 默认今天。

## provider=mock 与 provider=qmt

默认 `provider=mock`，用于测试和 dry-run。`provider=qmt` 时才尝试 QMT Historical Provider；无 xtquant 环境时继承阶段十五的跳过/失败隔离逻辑，不崩溃。

## cache hit / miss / fetched

已有覆盖返回 hit；缺失返回 miss 并尝试 provider 拉取，成功写入后记为 fetched；失败按 symbol 隔离，除非 `--fail-fast`。

## scheduled pipeline 启用

```bash
py scripts/run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 10 --warmup-frequency 1d --cache-root market_data_test_stage16
```

## register_daily_pipeline_task.py 生成计划任务

```bash
py scripts/register_daily_pipeline_task.py --warmup-universe --warmup-provider mock --universe-lookback-days 10 --warmup-frequency 1d --cache-root market_data --time 15:30
```

默认不传 `--execute`，只生成 dry-run 预览。

## 与项目总路线文档的关系

阶段十六开始引入 `docs/qmt-ai-trading-project-roadmap.md` 作为后续开发必读总文档，架构细节继续参考 `docs/qmt-ai-trading-architecture.md`。

## 安全边界

当前阶段不调用 xttrader、不下单、不实盘、不查询资金/持仓/订单/成交、不真实发送通知。
