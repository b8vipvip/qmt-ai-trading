# Approval / Paper Trading 操作手册

## Human Approval
Approval 是 TradeIntent 和 Risk Gate 之后的人工确认层。`PENDING` 表示等待人工；`APPROVED` 表示可进入后续 paper 候选；`REJECTED` 表示阻断。

## approval_cli.py
- `py scripts/approval_cli.py list --root approvals`
- `py scripts/approval_cli.py show --approval-id <id> --root approvals`
- `py scripts/approval_cli.py approve --approval-id <id> --decided-by local_user --root approvals`
- `py scripts/approval_cli.py reject --approval-id <id> --decided-by local_user --root approvals`

## Paper Trading
Paper Trading 只写本地 `paper_orders/`，不等于真实订单。只有 `APPROVED` approval 且 `RiskDecision allowed=True` 才能进入 paper。

## paper_trading_cli.py
`py scripts/paper_trading_cli.py submit-approved --approval-id <id> --approval-root approvals --paper-root paper_orders`

当前阶段仍不实盘、不调用 QMT 交易接口、不调用 xttrader、不查询真实资金/持仓/订单/成交、不真实发送通知、不自动 approve、不自动 paper submit、不自动 live submit、不真实下单。
