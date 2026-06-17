# 阶段十二：Historical Data Cache / Local Market Data Store

阶段十二新增本地历史行情缓存层，用于让回测、影子回放和后续研究任务优先读取本地已保存的 K 线数据。本阶段只使用 mock provider，不接真实 QMT、不请求外部行情接口、不实盘、不下单。

## 为什么先用本地文件缓存而不是数据库

当前目标是建立稳定的数据契约和缓存命中逻辑，而不是引入重型基础设施。JSONL 文件具备以下优点：

- 仅依赖 Python 标准库，便于在 Windows 本地直接运行。
- 每行一个 bar，追加、去重、排查都很直观。
- 后续可平滑迁移到 CSV、Parquet、SQLite、DuckDB 或 PostgreSQL。
- 不需要额外服务进程，降低阶段十二的部署风险。

## LocalBarStore 职责

`LocalBarStore` 是本地历史 K 线缓存的读写入口，默认根目录是 `market_data/`。

主要职责：

- 按 `symbol/frequency` 创建本地目录。
- 保存 JSONL 格式的 bars。
- 维护每个 `symbol/frequency` 的 `metadata.json`。
- 根据 `BarQuery` 读取本地区间数据。
- 判断缓存是否覆盖查询区间。
- 返回缺失区间，供后续增量补齐。
- 支持清理单个 symbol 或 symbol/frequency 缓存。

## 数据结构说明

### BarQuery

描述一次历史 K 线查询：

- `symbols`：证券代码列表。
- `start_date` / `end_date`：查询日期区间。
- `frequency`：周期，例如 `1d`。
- `adjust`：复权参数，当前保留。
- `provider`：数据来源标识。
- `metadata`：扩展字段。

### BarCacheMetadata

描述本地某个 `symbol/frequency` 缓存文件：

- `symbol` / `frequency`：缓存维度。
- `start_date` / `end_date`：本地覆盖区间。
- `row_count`：本地行数。
- `path`：JSONL 文件路径。
- `provider`：写入数据的 provider。
- `created_at` / `updated_at`：缓存时间。
- `metadata`：格式等扩展信息。

### BarCacheResult

描述一次缓存查询或拉取结果：

- `query`：原始查询。
- `hit`：是否完全命中本地缓存。
- `missing_ranges`：缺失区间。
- `bars`：返回的 K 线列表。
- `metadata`：相关缓存 metadata。
- `message`：结果说明。

## cache hit / cache miss / missing ranges

- cache hit：本地 metadata 覆盖 `start_date` 到 `end_date`，直接读取 JSONL。
- cache miss：本地没有 metadata，或本地覆盖区间不足。
- missing ranges：当前先返回查询区间，后续可细化为按交易日拆分的增量缺口。

本阶段在部分缺失时采用简单策略：重新用 provider 获取整个查询区间，保存时按日期去重覆盖，保证结果稳定。

## mock provider 的用途

`MockHistoricalDataProvider` 生成稳定、可重复的模拟 K 线数据，用于：

- 测试缓存命中和缓存未命中逻辑。
- 验证脚本参数和本地文件写入。
- 支持回测链路在没有真实行情源时运行。

它不会访问 QMT，不会访问任何外部 API，也不会下载真实行情。

## 后续如何接 QMT historical provider

后续可以新增 `QMTHistoricalDataProvider`，实现与 `HistoricalDataProvider` 相同的 `get_bars(query)` 接口：

1. 从 `BarQuery` 读取 symbol、frequency、date range。
2. 调用 QMT 只读历史行情接口。
3. 转换为 `MarketBar` 列表。
4. 交给 `fetch_historical_bars` 写入 `LocalBarStore`。

实盘交易接口不得在 provider 中出现，历史 provider 只负责只读行情。

## 后续如何升级数据库

当 JSONL 文件不能满足性能或并发需求时，可以按以下顺序升级：

1. SQLite：单机零服务，适合索引查询和轻量 SQL。
2. DuckDB：适合 Parquet、研究分析和批量回测。
3. PostgreSQL：适合多进程、多用户、集中式部署。

升级时应保留 `BarQuery` / `BarCacheResult` 契约，避免策略层感知存储实现变化。

## Git 与安全边界

- `market_data/` 和 `data_cache/` 不提交 Git。
- `*.bars.jsonl`、`*.bars.csv`、`*.bars.parquet` 不提交 Git。
- 当前阶段不真实下载、不实盘、不下单、不发送通知。
- 不保存 token、账号、密钥或真实账户数据。
