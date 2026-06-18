# 阶段二十二：Paper Trading / QMT dry-run 适配

## 阶段二十二目标

阶段二十二在 Human Approval 之后加入本地 paper order 生命周期模拟，验证从 `APPROVED ApprovalRequest`、Risk Gate 已允许的 `TradeIntent` 到 `PaperOrder` 和 `PaperExecutionReport` 的闭环。

## Paper Trading 与真实下单的区别

Paper Trading 只写入本地 `paper_orders/` JSON 文件，不等于 QMT 实盘下单。当前阶段不调用 QMT、不调用 `xttrader`、不查询资金/持仓/订单/成交、不实盘、不下单。

## PaperOrder / PaperExecutionReport / PaperSubmitResult

- `PaperOrder`：记录 approval_id、run_id、symbol、side、quantity、价格、状态时间戳、拒单原因和 `dry_run=True`。
- `PaperExecutionReport`：汇总一次 approval paper 提交产生的订单数量、filled/rejected/cancelled 计数和安全提示。
- `PaperSubmitResult`：服务层返回对象，包含 allowed、success、orders、report、message 和非敏感 metadata。

## paper_orders/ 本地文件结构

```text
paper_orders/
├─ paper_order_<paper_order_id>.json
└─ paper_report_<report_id>.json
```

`paper_orders/` 是本地运行产物，已加入 `.gitignore`，不得提交。文件不得包含 token、账号、密钥或真实敏感信息。

## paper_trading_cli.py 使用方式

```powershell
py scripts/paper_trading_cli.py submit-approved --approval-id <id> --approval-root approvals --paper-root paper_orders
py scripts/paper_trading_cli.py list --paper-root paper_orders
py scripts/paper_trading_cli.py show --paper-order-id <id> --paper-root paper_orders
py scripts/paper_trading_cli.py cancel --paper-order-id <id> --paper-root paper_orders --reason "manual cancel"
```

所有输出都会提示：`Paper trading only. No QMT order has been submitted.`

## Approval 与阻断规则

`approval_cli.py approve` 只把 approval 标记为 `APPROVED`，不会自动触发 paper trading，也不会自动下单。`submit-approved` 必须要求 approval status 为 `APPROVED`。`PENDING`、`REJECTED`、`CANCELLED`、`EXPIRED` approval 会阻断 paper trading。

Paper Trading 不绕过 Risk Gate。approval request 中必须存在 `trade_intents`，且必须存在 `risk_decisions` 并全部 `allowed=True`；任一 `RiskDecision allowed=False` 或缺失 risk_decisions 都会阻断 paper trading。

## HOLD 处理

`HOLD` intent 只记录为 `CREATED` / HOLD paper 记录，不进入 submitted/filled 状态，不代表真实订单。

## 阶段二十二通过后的下一阶段计划

阶段二十三：实盘前安全审计。目标是在 Paper Trading 闭环之后建立 go/no-go 安全审计报告，检查 live trading 开关、Human Approval、Risk Gate、Paper Trading、QMT Gateway、敏感信息、仓位限制、日志和配置，默认输出 NO-GO。阶段二十三仍不实盘、不调用 `xttrader`、不真实下单。
