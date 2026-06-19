# 阶段五十二：最终只读锁定复核与归档一致性核验

Stage52 是最终只读锁定复核与归档一致性核验。它在 Stage51 最终只读封版复核与材料归档锁定基础上，只读取本地 Stage48、Stage49、Stage50、Stage51 证据，生成最终只读锁定复核包、归档一致性核验包、人工闭环复查包和下一阶段只读检查计划。

## 安全边界

- Stage52 不等于实盘授权。
- Stage52 不调用 `xttrader`，不调用 QMT 交易接口。
- Stage52 不真实下单。
- Stage52 不查询资金、持仓、订单、成交。
- Stage52 不真实发送通知。
- Stage52 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_LOCK_CONSISTENCY_REVIEW` 只表示最终只读锁定复核与归档一致性核验材料可供人工复核，不代表实盘授权。

## 输出材料

默认输出目录为 `live_lock_consistency_stage52/`，运行产物不提交：

- `live_lock_consistency.md` / `live_lock_consistency.json`
- `archive_consistency.md` / `archive_consistency.json`
- `human_closure_recheck.md` / `human_closure_recheck.json`
- `next_readonly_check_plan.md` / `next_readonly_check_plan.json`

## 决策语义

- `NO_GO`：存在 CRITICAL，或 Stage48/49/50/51 任一材料明确 `NO_GO` / critical > 0。
- `NEED_MORE_EVIDENCE`：缺少证据但没有 CRITICAL；Stage51 `NEED_MORE_EVIDENCE` 且 critical=0 时，Stage52 仍可生成只读材料并保持该状态。
- `READY_FOR_LOCK_CONSISTENCY_REVIEW`：只表示最终只读锁定复核与归档一致性核验材料可供人工复核；不是实盘授权。

## 下一阶段预告

Stage53 建议为“最终只读归档核验与锁定材料复核”。Stage53 仍不能直接实盘，只能继续做最终只读归档核验、锁定材料复核、人工闭环复查或更严格的灰度前检查。Stage53 仍不能自动 approve，不能调用 `xttrader`，不能查询真实账户，不能真实通知。
