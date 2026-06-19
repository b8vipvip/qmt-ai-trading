# 阶段四十五：灰度前只读运行手册与人工流程演练

Stage45 在 Stage44 只读环境快照基础上，生成灰度前只读运行手册、人工流程演练包和异常处理流程清单，用于未来人工会议、运行前培训、异常处理演练和 go/no-go 流程复核。

## 安全边界

- Stage45 不等于实盘授权。
- Stage45 不调用 xttrader。
- Stage45 不调用 QMT 交易接口。
- Stage45 不真实下单。
- Stage45 不查询资金、持仓、订单、成交。
- Stage45 不真实发送通知。
- Stage45 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_RUNBOOK_REVIEW` 只表示运行手册材料可供人工复核，不代表可以实盘。

## 输出材料

默认输出目录为 `live_runbook_stage45/`，运行产物不提交：

- `live_runbook.md` / `live_runbook.json`
- `manual_rehearsal.md` / `manual_rehearsal.json`
- `incident_playbook.md` / `incident_playbook.json`

## 决策语义

- `NO_GO`：存在 CRITICAL 或明确阻断，例如 Stage41 `BLOCKED`、Stage42/43/44 `NO_GO` 或 critical > 0。
- `NEED_MORE_EVIDENCE`：缺少证据但没有 CRITICAL；Stage44 `NEED_MORE_EVIDENCE` 且 critical=0 时，Stage45 仍可生成只读材料并保持该状态。
- `READY_FOR_RUNBOOK_REVIEW`：只表示运行手册材料可供人工复核；不是实盘授权。

## 人工演练范围

人工流程演练包覆盖演练前检查、只读运行手册复核、Human Approval 边界、Risk Gate 边界、Scheduler preview、异常场景演练和 go/no-go 会议材料确认。

异常处理清单覆盖数据缓存不足、Risk Gate 拒绝、Human Approval 缺失、Scheduler preview 异常、报告生成失败、发现真实交易 marker、发现敏感文件或运行产物误提交、发现 `scripts/sync_all.ps1` 被修改。

## Stage46 预告

Stage46 建议名称为“阶段四十六：灰度前运行手册复核与人工演练签字封版”。Stage46 仍不能直接实盘，只能继续做运行手册复核、人工演练签字、配置冻结复查、异常演练结果和更严格的只读检查；仍不能自动 approve，不能调用 xttrader，不能查询真实账户，不能真实通知。
