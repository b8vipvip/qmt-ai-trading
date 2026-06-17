# 阶段十四：QMT Historical Provider 实机联调与字段校准

## 阶段目标

阶段十四在阶段十三 `QmtHistoricalDataProvider` 的基础上，增加 QMT / MiniQMT 历史行情读取的实机诊断、样本拉取、字段结构检查、字段映射校准和数据质量报告工具。本阶段仍然只读取历史行情并写入本地缓存，不接真实交易。

## 为什么需要实机联调和字段校准

不同 MiniQMT / `xtquant.xtdata` 版本、不同周期或返回接口可能使用不同字段名，例如 `open`、`openPrice`、`open_price`。字段校准工具用于在实机环境中确认原始数据结构，避免缓存写入错误字段。

## 无 xtquant 环境的预期表现

当前 Python 环境没有接入 MiniQMT / `xtquant` 时，诊断脚本会输出 `xtdata_available=False`，并提示安装或切换到 MiniQMT Python 环境；脚本不应堆栈崩溃。

## QMT 字段别名映射

- `datetime`: `datetime` / `time` / `date` / `index`
- `open`: `open` / `openPrice` / `open_price`
- `high`: `high` / `highPrice` / `high_price`
- `low`: `low` / `lowPrice` / `low_price`
- `close`: `close` / `closePrice` / `close_price`
- `volume`: `volume` / `vol`
- `amount`: `amount` / `turnover`

## 诊断数据结构

- `QmtRuntimeInfo`: xtdata 是否可导入、模块路径、connect 能力、连接结果、可用函数摘要。
- `QmtSampleFetchResult`: 样本拉取结果、行数、原始字段、归一化数量、缓存路径。
- `QmtFieldCalibration`: 原始字段、映射字段、缺失必需字段、样本行。
- `QmtDataQualityReport`: 行数、首尾时间、OHLC 缺失、零成交量、重复时间、排序状态。

## check_qmt_data_provider.py 使用方式

```powershell
py scripts/check_qmt_data_provider.py
py scripts/check_qmt_data_provider.py --diagnose
py scripts/check_qmt_data_provider.py --diagnose --print-functions
py scripts/check_qmt_data_provider.py --fetch-sample --cache-root market_data_qmt_check
py scripts/check_qmt_data_provider.py --diagnose --write-report --report-path qmt_runtime_report.md
```

默认只检查 `xtquant.xtdata` 是否可导入。只有显式传入 `--fetch-sample` 才尝试读取小样本。

## qmt_fetch_sample_calibrate.py 使用方式

```powershell
py scripts/qmt_fetch_sample_calibrate.py --symbol 510300.SH --start 2024-01-01 --end 2024-01-10 --frequency 1d --cache-root market_data_qmt_check
```

该脚本使用 `QmtHistoricalDataProvider` 和 `LocalBarStore`，输出 runtime info、字段校准、归一化 bars 数量、缓存路径和数据质量报告。

## 如何确认 cache hit / miss

首次运行样本拉取时，如果缓存目录没有覆盖目标区间，会显示 cache miss 并写入本地 JSONL。第二次使用同一 symbol、frequency 和日期区间运行时，应显示 cache hit。

## 如何检查 market_data_qmt_check/

`market_data_qmt_check/` 是本阶段实机样本缓存目录，已加入 `.gitignore`。可检查目录下的 symbol/frequency 子目录、`metadata.json` 和 `*.bars.jsonl`。

## 当前阶段安全边界

本阶段不调用 `xttrader`，不查询资金、持仓、订单、成交，不下单、不撤单、不发送邮件 / Telegram / 企业微信，不接实盘交易。

## 后续建议

后续阶段可在确认字段稳定后，将历史数据补齐接入 Windows Scheduler，每日自动补历史行情缓存。
