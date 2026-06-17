# 阶段五：Data Hub 标准化

## 职责

Data Hub 是 Strategy、Research、Agent 后续统一的数据入口，负责证券代码标准化、ETF 默认候选池、只读行情入口和缓存接口占位。阶段五不做 UI、不连接真实实盘、不调用真实下单，也不破坏已跑通的 QMT Gateway、Risk Gate 和 ETF Rotation Strategy Engine。

## Symbol 标准化规则

统一内部格式为 `510300.SH` / `159915.SZ`：

- 支持 `510300.SH`、`159915.SZ` 后缀格式；
- 支持 `510300`、`159915` 纯六位代码，并按常见 A 股/ETF 前缀推断市场；
- 支持 `SH510300`、`SZ159915` 前缀格式；
- 支持 `sh.510300`、`sz.159915` 点分前缀格式；
- 标准化函数不依赖网络，也不会连接任何行情或交易接口。

## ETF universe 默认候选池

`qmt_ai_trading.datahub.etf_universe.get_default_etf_universe()` 内置少量常用 ETF 示例：

- `510300.SH` 沪深300ETF
- `510500.SH` 中证500ETF
- `159915.SZ` 创业板ETF
- `512100.SH` 中证1000ETF
- `588000.SH` 科创50ETF

该列表只作为默认候选池示例，不构成投资建议。后续可在同一接口后接入 QMT 本地行情、AkShare、Tushare、BaoStock 或人工维护的研究池。

## market_data 与 gateway adapter

`qmt_ai_trading.datahub.market_data` 提供：

- `get_latest_price(symbol)`：优先通过 `qmt_ai_trading.gateway.qmt_market` 只读 adapter 获取最新价，并转换为 `LatestPrice`；当 QMT 不可用或无真实数据时返回 `None`。
- `get_bars(symbol, period="1d", count=100)`：优先通过 `qmt_ai_trading.gateway.qmt_market` 只读 adapter 获取 K 线，并转换为 `MarketBar` 列表；当 QMT 不可用或无真实数据时返回空列表。

模块 import 时不会连接 QMT，只有函数被调用时才懒加载 gateway adapter。异常会被 Data Hub 收敛为 `None` 或空列表，避免 Strategy / Research / Agent 直接暴露在 QMT 环境差异中。

## 当前阶段边界

阶段五不连接网络、不接真实数据库、不硬编码真实路径、不提交缓存数据。所有新增模型使用 dataclass 和标准库实现，不引入重依赖。

## 缓存后续规划

`qmt_ai_trading.datahub.cache` 仅提供接口占位：

- `get_cache_path(...)`
- `load_cached_bars(...)`
- `save_cached_bars(...)`

默认路径位于本地 `data/cache/datahub` 下，当前不会实际写入行情数据。后续可按运行环境选择 parquet、duckdb、sqlite 或 postgres 作为缓存后端。

## Strategy / Research / Agent 访问约定

后续 Strategy、Research、Agent 都应通过 Data Hub 获取 universe、行情和缓存数据，不应绕过 Data Hub 直接散落调用 QMT、AkShare、Tushare、BaoStock 或本地数据库。阶段五已为 ETF Rotation Strategy Engine 增加 `build_candidates_from_universe(...)` adapter，使策略可以从 Data Hub 默认 ETF universe 生成 `ETFCandidate`，并继续输出 dry-run `TradeIntent`。
