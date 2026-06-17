# Stage 13 - QMT Historical Provider Adapter

## 职责

QMT Historical Provider 负责把阶段十二的 `HistoricalDataProvider` / `LocalBarStore` 缓存层接入本机 MiniQMT / QMT 的 `xtquant.xtdata` 历史行情读取能力。当前阶段只读取历史行情并写入本地缓存，不接真实交易。

## 可选依赖设计

`xtquant` 只存在于安装并配置好 MiniQMT / QMT 的本地 Python 环境中，因此 provider 必须是可选依赖。项目默认仍使用 mock provider；没有 `xtquant` 时，导入 Data Hub、运行旧测试和 mock 缓存脚本都不能崩溃。

因此 `qmt_ai_trading.datahub.qmt_provider` 不在顶层执行 `from xtquant import xtdata`，而是在显式创建或使用 `QmtHistoricalDataProvider` 时通过内部 `_import_xtdata()` 延迟导入。

## 历史行情缓存流程

1. 根据 `BarQuery` 先查询 `LocalBarStore`。
2. cache hit 时直接返回本地 bars，不调用 QMT。
3. cache miss 时调用 `xtdata.download_history_data(symbol, period, start_time=YYYYMMDD, end_time=YYYYMMDD)`。
4. 再调用 `xtdata.get_market_data_ex(...)`；如果本地环境只支持旧接口，则兼容 `xtdata.get_market_data(...)`。
5. 将 pandas DataFrame、dict/list 等返回结构转换成 `MarketBar`。
6. 保存到 `market_data/` 或用户指定的 cache root。

## 检查 QMT provider

默认只检查能否导入 `xtquant.xtdata`，不下载行情、不调用交易接口：

```powershell
py scripts/check_qmt_data_provider.py
```

尝试调用 `xtdata.connect()`（如果本地 xtdata 提供该函数）：

```powershell
py scripts/check_qmt_data_provider.py --try-connect
```

只有显式传入 `--fetch-sample` 才拉取一小段样例历史行情，并保存到 `market_data_qmt_check/`：

```powershell
py scripts/check_qmt_data_provider.py --fetch-sample --symbol 510300.SH --start 2024-01-01 --end 2024-01-10
```

## 使用 fetch_history_cache.py

mock 模式仍是默认行为：

```powershell
py scripts/fetch_history_cache.py --symbols 510300.SH,510500.SH --start 2024-01-01 --end 2024-01-10 --frequency 1d --cache-root market_data --provider mock
```

QMT 模式需要本机 MiniQMT / QMT 已启动，并且当前 Python 环境能导入 `xtquant.xtdata`：

```powershell
py scripts/fetch_history_cache.py --symbols 510300.SH,510500.SH --start 2024-01-01 --end 2024-01-10 --frequency 1d --cache-root market_data --provider qmt
```

脚本会输出 cache hit / cache miss、返回或保存条数、本地路径和状态消息。

## 安全边界

当前阶段不实盘、不下单、不撤单、不查询资金、不查询持仓，不导入或调用 `xttrader`。后续阶段如需接入实时行情、账户或交易安全层，应在独立阶段中增加更严格的权限、风控和只读/禁交易边界。
