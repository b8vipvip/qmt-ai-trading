# Stage 15: Scheduled Pipeline Historical Cache Warmup

## 目标

阶段十五把“历史行情缓存自动补全”接入每日 scheduled pipeline：在 ETF 策略运行前，先检查 ETF universe 在本地 `market_data/` 下的历史 K 线缓存是否覆盖指定日期区间；缺失时再通过 historical provider 获取并写入本地缓存。

本阶段仍然是安全 dry-run / shadow 阶段：不调用 `xttrader`，不下单，不查询资金、持仓、订单或成交。

## 为什么要先预热历史行情缓存

每日策略运行依赖稳定、可复现的历史行情输入。把缓存预热放在 scheduled pipeline 前面，可以：

- 提前发现历史行情缺口；
- 避免策略运行过程中临时缺数据；
- 将 provider 访问与策略逻辑解耦；
- 在无 QMT 环境时仍允许 dry-run pipeline 继续运行；
- 为后续真实 QMT 环境每日补齐 ETF universe 行情打基础。

## 数据结构

### CacheWarmupRequest

`CacheWarmupRequest` 描述一次缓存预热请求，包含：

- `symbols`：需要检查和补齐的标的列表；
- `start_date` / `end_date`：目标历史区间；
- `frequency`：周期，例如 `1d`；
- `provider`：`mock` 或 `qmt`；
- `cache_root`：本地缓存根目录；
- `adjust`：复权参数，占位透传；
- `fail_fast`：单个 symbol 失败后是否立即中止；
- `metadata`：附加元数据。

### CacheWarmupResult

`CacheWarmupResult` 汇总本次预热结果，包含 provider、缓存目录、日期区间、symbol 总数、命中数、缺失数、拉取成功数、失败数、跳过数和逐 symbol 明细。

## 状态含义

- `hit`：本地缓存已经覆盖请求区间，不重复访问 provider；
- `miss`：本地缓存缺失或覆盖不足；
- `fetched`：发生 miss 后已从 provider 获取并保存到本地缓存；
- `skipped`：当前环境不满足 provider 条件，例如 `provider=qmt` 但 `xtquant.xtdata` 不可用；
- `failed`：该 symbol 预热失败。`fail_fast=False` 时会继续处理后续 symbol。

## 手动预热脚本

Mock 模式：

```powershell
py scripts/warmup_history_cache.py --symbols 510300.SH,510500.SH --start 2024-01-01 --end 2024-01-10 --frequency 1d --provider mock --cache-root market_data_test_stage15
```

QMT historical provider 模式：

```powershell
py scripts/warmup_history_cache.py --symbols 510300.SH,510500.SH --start 2024-01-01 --end 2024-01-10 --frequency 1d --provider qmt --cache-root market_data
```

如果无 `xtquant.xtdata`，QMT 模式会输出可读 warning / skipped 结果，不会调用交易接口。

## Scheduled pipeline 使用方式

```powershell
py scripts/run_scheduled_daily_pipeline.py --warmup-cache --warmup-provider mock --warmup-start 2024-01-01 --warmup-end 2024-01-10 --warmup-frequency 1d --cache-root market_data_test_stage15
```

`--warmup-cache` 未传入时保持旧行为。传入后，脚本会在 daily pipeline 前对默认 ETF universe 执行缓存预热，并把 summary 写入 `logs/daily_pipeline/`。

## 注册计划任务使用方式

默认仍是 dry-run 预览，不传 `--execute` 不会真实注册 Windows 计划任务：

```powershell
py scripts/register_daily_pipeline_task.py --warmup-cache --warmup-provider mock --warmup-start 2024-01-01 --warmup-end 2024-01-10 --warmup-frequency 1d --cache-root market_data --time 15:30
```

生成的计划任务命令会包含 warmup 参数。未传 `--warmup-cache` 时保持旧注册命令格式。

## provider=mock 与 provider=qmt

- `mock`：默认 provider，生成确定性的本地测试 K 线，适合无 QMT 环境测试；
- `qmt`：仅使用 QMT historical provider / `xtquant.xtdata` 获取历史行情；不导入或调用 `xttrader`，不进行交易相关查询。

## 无 xtquant 环境的预期行为

当 `provider=qmt` 且当前 Python 环境无法 import `xtquant.xtdata` 时，cache warmup 会记录 skipped/failed item 和可读消息；scheduled pipeline 不会因为该条件崩溃，仍可继续 dry-run 策略与报告流程。

## 安全边界

阶段十五不调用 `xttrader`、不下单、不实盘、不查询资金/持仓/订单/成交，也不真实发送邮件、Telegram 或企业微信通知。运行产物 `market_data/`、`logs/`、`reports/` 等保持为本地文件并被 `.gitignore` 排除。

## 后续阶段

后续可在真实 QMT 环境中把每日 ETF universe 的增量行情补齐接入生产级本地数据维护流程，并继续保持交易接口与行情缓存流程隔离。
