# 阶段四十六：灰度前运行手册复核与人工演练签字封版

Stage46 在 Stage45 只读运行手册与人工流程演练包基础上，生成运行手册复核包、人工演练签字封版材料和异常演练结果摘要，用于未来人工会议复核、签字归档和材料封版。

## 安全边界

- Stage46 不等于实盘授权。
- Stage46 不调用 xttrader。
- Stage46 不调用 QMT 交易接口。
- Stage46 不真实下单。
- Stage46 不查询资金、持仓、订单、成交。
- Stage46 不真实发送通知。
- Stage46 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_SIGNOFF_REVIEW` 只表示签字封版材料可供人工复核，不代表可以实盘。

## 输出材料

默认输出目录为 `live_signoff_stage46/`，运行产物不提交：

- `live_signoff.md` / `live_signoff.json`
- `manual_signoff.md` / `manual_signoff.json`
- `incident_rehearsal.md` / `incident_rehearsal.json`

## 决策语义

- `NO_GO`：存在 CRITICAL 或明确阻断，例如 Stage42/43/44/45 `NO_GO` 或 critical > 0。
- `NEED_MORE_EVIDENCE`：缺少证据但没有 CRITICAL；Stage45 `NEED_MORE_EVIDENCE` 且 critical=0 时，Stage46 仍可生成只读复核与签字材料并保持该状态。
- `READY_FOR_SIGNOFF_REVIEW`：只表示签字封版材料可供人工复核；不是实盘授权。

## 复核范围

运行手册复核包覆盖 Stage45 运行手册、人工流程演练、异常处理清单、安全声明、只读运行步骤、禁止动作、Risk Gate / Human Approval 边界、Scheduler preview、运行产物忽略规则和 go/no-go 材料状态。

人工演练签字封版材料覆盖演练主持人、风险负责人、运行负责人、配置冻结复核人和最终授权人签字项。每个签字项都写明“不代表实盘授权”和“未来真实执行仍需单独审批”。

异常演练结果摘要覆盖数据缓存不足、Risk Gate 拒绝、Human Approval 缺失、Scheduler preview 异常、报告生成失败、发现真实交易 marker、发现敏感文件或运行产物误提交、发现 `scripts/sync_all.ps1` 被修改。

## Stage47 预告

Stage47 仍不能直接实盘，只能继续做最终只读 go/no-go 材料汇总、人工签字核验、缺口列表或更严格的灰度前检查。Stage47 仍不能自动 approve，不能调用 xttrader，不能查询真实账户，不能真实通知。
