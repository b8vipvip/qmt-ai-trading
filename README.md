# A 股 QMT AI 量化研究项目

本项目基于 QMT / MiniQMT 构建 A 股量化研究、历史回测、参数优化、稳定性验证、交易信号和 dry-run 订单计划流程。新增的 AI 模块只参与策略研究，不具备实盘下单能力。

## 安全边界

- 项目默认且强制要求 `live_trading_enabled` 为 `false`。
- AI 只能读取历史行情、分析回测结果、生成研究策略、优化参数和输出 dry-run 信号。
- AI 生成策略必须同时提供 `backtest` 与 `generate_signal`，保存前会经过 AST 安全检查。
- AI 生成策略禁止导入 QMT 交易模块，禁止调用真实下单或撤单接口，禁止网络、文件和进程操作。
- `qmt_execute_manual_guard.py` 只是安全预检器，当前版本不会执行任何实盘交易。
- 本项目默认不执行实盘交易，任何研究结果均不构成投资建议。

## 项目结构

```text
ai_tools/
  ai_client.py             OpenAI-compatible API 客户端，从本地环境读取密钥
  ai_provider_pool.py      多供应商、多模型配置池
  ai_router_client.py      超时、错误分类与自动切换路由
  ai_api_logger.py         不含密钥和提示词的调用元数据日志
  ai_api_report.py         供应商与模型稳定性统计
  analyze_backtest.py      汇总收益、回撤、交易次数、稳定性和过拟合风险
  generate_strategy.py     根据分析报告生成并安全检查研究策略
  optimize_strategy.py     多时间段参数优化与稳定性评分
  iteration_runner.py      多轮回测、分析、生成、优化和最优结果保存
strategies/                AI 研究策略输出目录
qmt_backtest_ma.py         均线历史回测
qmt_optimize_ma.py         均线参数优化
qmt_stable_ma.py           多时间段稳定性筛选
qmt_generate_signal_ma.py  dry-run 信号生成
qmt_daily_dryrun.py        一键 daily dry-run
config.example.json        非敏感配置示例
.env.example               AI API 环境变量示例
```

运行数据会写入本地 `backtest_results/`、`signals/`、`logs/` 和 `runs/`，这些目录均不会提交到仓库。AI 生成的 `strategies/ai_strategy_*.py` 也作为运行产物忽略。

## 安装与本地配置

1. 安装并启动 QMT / MiniQMT，确认 QMT 自带 Python 能导入 `xtquant`。
2. 复制 `config.example.json` 为 `config.json`，填写本机 QMT 路径、账户标识和输出目录。不要提交 `config.json`。
3. 始终保持：

```json
"live_trading_enabled": false
```

4. 如需 AI 分析与策略生成，复制 `.env.example` 为 `.env`。一个 `.env` 即可管理多个 OpenAI-compatible AI API；每个供应商只需填写 API 地址、API Key 和英文逗号分隔的模型 ID 列表：

```dotenv
AI_PROVIDER_1_NAME=apihost
AI_PROVIDER_1_BASE_URL=https://apihost.cn/v1
AI_PROVIDER_1_API_KEY=your_api_key_here
AI_PROVIDER_1_MODELS=gpt-5.4-mini,gpt-5.4
```

继续按 `AI_PROVIDER_2_*`、`AI_PROVIDER_3_*` 添加供应商，编号必须从 1 连续递增。可用 `AI_TIMEOUT_SECONDS`、`AI_COOLDOWN_SECONDS` 和 `AI_MAX_RETRIES` 设置全局超时、冷却及重试次数。`.env` 已被 Git 忽略，禁止填写或提交真实 Key 到其他仓库文件。

### AI API 供应商池

路由器优先读取 `.env` 的 `AI_PROVIDER_N_*` 配置，并自动按 provider/model 轮询；遇到 401、403、429、超时或 5xx 时会冷却、重试或切换。旧版 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL` 以及 `ai_providers.local.json` 仅作为兼容备用，不再推荐维护 JSON 配置。

每次成功或失败调用的非敏感元数据写入 `logs/ai_api_calls.jsonl`，不记录完整密钥或提示词。查看 provider/model 成功率、平均耗时及错误原因统计：

```bash
python -m ai_tools.ai_api_report
```

报告同时保存为 `logs/ai_api_report.json` 和 `logs/ai_api_report.csv`。API 池仅服务于研究分析和 ETF 轮动解释，不参与实盘决策，不调用真实下单或撤单接口。

## Daily dry-run

使用 QMT 自带 Python 执行：

```bat
D:\国金证券QMT交易端\bin.x64\python.exe qmt_daily_dryrun.py
```

流程依次生成信号、生成 dry-run 订单计划、执行安全预检并写入每日状态和日志。该流程只打印和保存计划，不会下单。

## AI 模块使用

先运行现有回测，将 JSON 结果保存到 `backtest_results/`。然后可分步执行：

```bash
python -m ai_tools.analyze_backtest --input-dir backtest_results
python -m ai_tools.generate_strategy --analysis backtest_results/ai-analysis.json
python -m ai_tools.optimize_strategy --strategy strategies/ai_strategy_YYYYMMDD_HHMMSS.py --config config.json
```

`analyze_backtest` 同时输出 `ai-analysis.txt` 和 `ai-analysis.json`。`optimize_strategy` 根据 `config.json` 中的 `ai_iteration.validation_periods` 做多时间段验证，输出 `optimize-result.json`、`optimize-result.csv` 和 `best-result.json`。

执行完整多轮迭代：

```bash
python -m ai_tools.iteration_runner --config config.json --rounds 2
```

每轮结果保存在独立的 `runs/run_YYYYMMDD_HHMMSS_.../` 目录，包含回测结果、分析报告、生成策略副本、优化结果、最优结果和运行日志。全局最优结果保存为 `runs/best-result.json`。

## AI 策略接口

AI 生成的研究策略必须定义：

```python
PARAM_GRID = {"fast_window": [5, 10], "slow_window": [20, 30]}

def backtest(dates, closes, params):
    return {"profit_rate": 0.0, "max_drawdown": 0.0, "trade_count": 0}

def generate_signal(dates, closes, params):
    return {"signal": "HOLD", "target_position_pct": None, "reason": "research only"}
```

允许的信号仅用于 dry-run。生成策略不得包含真实交易执行逻辑。

## 提交与敏感数据

提交前检查 `git status`。不要提交以下内容：

- `config.json`、`.env` 或任何密钥；
- `logs/`、`signals/*.json`、`backtest_results/`、`runs/`；
- 本地账户信息、安装目录压缩包或其他运行产物。

## ETF / 板块轮动候选池

ETF 轮动模块位于 AI 情报分析之前，使用 QMT `xtdata` 的只读历史行情，对 `config.json` 中的 ETF 候选池进行流动性和回撤过滤，并按 5 日、20 日、60 日收益率、均线趋势、成交额、最大回撤和波动率评分。ETF 名称优先通过 QMT 合约信息读取，候选代码仅来自配置，不写死在筛选代码中。

主要文件：

- `data_tools/etf_universe.py`：读取并校验 ETF 候选池；
- `data_tools/market_regime.py`：根据配置的宽基指数判断 `bullish`、`sideways` 或 `bearish` 市场环境；
- `data_tools/etf_rotation_selector.py`：过滤、评分并选择 `top_n` 个 ETF，默认选择 1 个；
- `qmt_generate_signal_rotation.py`：将入选 ETF 转换为与 `qmt_plan_order_dryrun_v2.py` 兼容的 dry-run 信号；
- `qmt_backtest_etf_rotation.py`：执行每日或每周调仓的多时间段历史验证。

运行前，将 `config.example.json` 复制为本地 `config.json` 并按需修改 `etf_rotation.etf_pool`、评分权重和风控阈值。推荐运行顺序如下：

```powershell
D:\国金证券QMT交易端\bin.x64\python.exe data_tools\market_regime.py
D:\国金证券QMT交易端\bin.x64\python.exe data_tools\etf_rotation_selector.py
D:\国金证券QMT交易端\bin.x64\python.exe qmt_generate_signal_rotation.py
D:\国金证券QMT交易端\bin.x64\python.exe qmt_plan_order_dryrun_v2.py
D:\国金证券QMT交易端\bin.x64\python.exe qmt_backtest_etf_rotation.py
```

运行输出写入已忽略的 `signals/` 与 `backtest_results/`。当市场偏空时，轮动信号只会输出 `SELL_SIGNAL` 或 `HOLD`；市场偏多且评分达到阈值时才输出 `BUY_SIGNAL`。

### ETF 轮动安全边界

- ETF 轮动只生成量化候选池、评分、历史回测结果和 dry-run 信号，不执行实盘交易；
- 模块只使用 `xtdata` 读取行情，不连接真实交易执行接口；
- 不会下单或撤单，且仍强制要求 `live_trading_enabled` 保持为 `false`；
- `signals/etf_scores.json`、`signals/etf_scores.csv`、`signals/selected_etf.json`、`signals/market_regime.json` 和 `backtest_results/` 均为本地运行产物，不应提交。

## 助手诊断日志

每次更新、测试、dry-run 或 AI 研究后，如需让 ChatGPT 协助分析，只需使用 QMT 自带 Python 运行只读诊断收集器：

```powershell
& "D:\国金证券QMT交易端\bin.x64\python.exe" "D:\AI\qmt\qmt_collect_diagnostics.py"
```

然后将以下两个已脱敏文件发给 ChatGPT：

```text
D:\AI\qmt\logs\assistant_diagnostic_latest.md
D:\AI\qmt\logs\assistant_diagnostic_latest.json
```

收集器会同时保留带时间戳的报告，汇总 Git、配置安全状态、更新检查、ETF dry-run、AI 研究/API 稳定性与最近产物。它不会读取 `.env` 内容、不会输出完整 API Key 或资金账号、不会修改实盘开关，也不会执行任何交易操作。
