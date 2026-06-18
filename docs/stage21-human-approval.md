# 阶段二十一：Human Approval 人工确认层

## 阶段二十一目标

在 `TradeIntent` 生成并完成 Risk Gate 校验之后、进入 Paper Trading 或未来 Live Trading 之前，加入人工审批对象、本地审批文件、CLI 审批流程和审批状态检查。默认只生成 `PENDING` approval，不自动批准。

## 为什么需要 Human Approval

Human Approval 是实盘前的人工授权闸门，用于防止 dry-run 信号、fallback/mock 数据、策略异常或操作误触直接进入 paper/live 执行链路。Approval 只决定是否允许继续进入后续执行模拟层，不改变 Risk Gate 结论，也不绕过风控。

## ApprovalRequest / ApprovalDecision / ApprovalCheckResult

- `ApprovalRequest`：保存审批编号、pipeline run_id、创建/过期时间、状态、TradeIntent、RiskDecision、数据源决策、confidence、摘要和非敏感 metadata。
- `ApprovalDecision`：保存 approve/reject/cancel 动作、审批人、审批时间、备注和动作后的状态。
- `ApprovalCheckResult`：供后续 paper/live 适配层检查，只有 `APPROVED` 才允许继续；`PENDING`、`REJECTED`、`EXPIRED`、`CANCELLED` 均阻断。

## approvals/ 本地文件结构

审批文件默认保存到 `approvals/`：

```text
approvals/
├─ approval_<approval_id>.json
└─ approval_<approval_id>.decision.json
```

`approvals/` 是本地运行产物，已加入 `.gitignore`，不得提交。审批文件不得包含 token、账号、密钥或真实敏感信息。

## approval_cli.py 使用方式

```powershell
py scripts/approval_cli.py list --root approvals
py scripts/approval_cli.py show --approval-id <id> --root approvals
py scripts/approval_cli.py approve --approval-id <id> --decided-by local_user --comment "approved for paper review only" --root approvals
py scripts/approval_cli.py reject --approval-id <id> --decided-by local_user --comment "reject reason" --root approvals
py scripts/approval_cli.py cancel --approval-id <id> --decided-by local_user --comment "cancel reason" --root approvals
```

CLI 只修改本地 approval JSON；approve 只是把 request 标记为 `APPROVED`，不代表下单。

## run_daily_pipeline.py --create-approval 使用方式

```powershell
py scripts/run_daily_pipeline.py --data-source-mode cached --cache-root market_data --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 1 --create-approval --approval-root approvals
```

默认不创建 approval。传入 `--create-approval` 且 pipeline 生成 TradeIntent 时，才创建 pending approval request；没有 TradeIntent 时不创建，并输出原因。

## scheduled pipeline --create-approval 使用方式

```powershell
py scripts/run_scheduled_daily_pipeline.py --warmup-universe --warmup-provider mock --universe-lookback-days 40 --warmup-frequency 1d --cache-root market_data --data-source-mode cached --research-start 2026-05-09 --research-end 2026-06-18 --research-frequency 1d --min-bars 20 --cached-strategy-top-n 1 --create-approval --approval-root approvals
```

计划任务 dry-run 预览也可包含 `--create-approval`、`--approval-root`、`--approval-expires-hours`。

## 安全说明

Approval is not an order. No QMT order has been submitted.

Pending approval; execution is blocked.

当前阶段不调用 QMT、不调用 `xttrader`、不查询资金/持仓/订单/成交、不实盘、不下单、不真实发送通知。Approval 只影响执行授权，不绕过 Risk Gate。

## 阶段二十一通过后的下一阶段计划

阶段二十二：Paper Trading / QMT dry-run 适配。目标是在 Human Approval 之后加入 paper order 生命周期模拟，记录 submitted / filled / cancelled / rejected 等状态，验证从 approved TradeIntent 到 paper order 的完整闭环。阶段二十二仍不实盘、不调用 `xttrader`、不真实下单。
