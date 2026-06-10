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

4. 如需 AI 分析与策略生成，复制 `.env.example` 为 `.env`，只在本机填写：

```dotenv
OPENAI_API_KEY=本地密钥
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

AI 客户端也支持直接读取同名环境变量。仓库不会保存真实 API Key。所有新增脚本使用兼容 QMT Python 3.6 的语法。

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
