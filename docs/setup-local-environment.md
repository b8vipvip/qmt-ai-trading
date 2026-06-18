# 本地环境准备手册

## Windows 本地运行前提
建议在 Windows PowerShell 中进入项目目录 `D:\AI\qmt`，安装 Python 3.10+。可选使用 `py -m venv .venv` 创建虚拟环境并安装 pytest：`py -m pip install pytest`。

## 项目目录说明
- `qmt_ai_trading/`：核心 Python 包。
- `scripts/`：本地 dry-run CLI。
- `docs/`：阶段文档和运行手册。
- `tests/`：验收测试。
- `market_data/`、`reports/`、`logs/`、`approvals/`、`paper_orders/`：本地运行产物，不提交。

## QMT / MiniQMT / xtquant
QMT、MiniQMT、xtquant 只在数据联调阶段可选；默认不需要真实 QMT 环境即可跑 mock / dry-run 验收。当前阶段仍不实盘、不调用 QMT 交易接口、不调用 xttrader、不查询真实资金/持仓/订单/成交、不真实发送通知、不自动 approve、不自动 paper submit、不自动 live submit、不真实下单。

## 敏感信息
不要提交 `.env`、Token、账号、密钥、数据库、缓存数据。
