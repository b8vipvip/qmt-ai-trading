# 阶段四十九：补证后只读复核与最终材料一致性检查

Stage49 是补证后只读复核与最终材料一致性检查。它在 Stage48 最终只读材料归档与缺口补证计划基础上，生成补证后只读复核框架、最终材料一致性检查、人工核验复查和下一轮灰度前检查计划。

## 安全边界

- Stage49 不等于实盘授权。
- Stage49 不调用 xttrader，不调用 QMT 交易接口。
- Stage49 不真实下单，不查询资金/持仓/订单/成交。
- Stage49 不真实发送通知，不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_CONSISTENCY_REVIEW` 只表示补证后只读复核与一致性材料可供人工复核，不代表可以实盘。

## 输出材料

默认输出目录为 `live_consistency_stage49/`，运行产物不提交：

- `live_consistency.md` / `live_consistency.json`
- `material_consistency.md` / `material_consistency.json`
- `human_recheck.md` / `human_recheck.json`
- `next_gray_check_plan.md` / `next_gray_check_plan.json`

## 决策语义

- `NO_GO`：存在 CRITICAL，或 Stage45/46/47/48 任一材料明确 NO_GO / critical > 0。
- `NEED_MORE_EVIDENCE`：缺少证据但没有 CRITICAL；Stage48 `NEED_MORE_EVIDENCE` 且 critical=0 时，Stage49 仍可生成只读复核与一致性材料并保持该状态。
- `READY_FOR_CONSISTENCY_REVIEW`：只表示补证后只读复核与一致性材料可供人工复核；不是实盘授权。

## 下一阶段预告

Stage50 建议为“最终归档复核与材料一致性封版”。Stage50 仍不能直接实盘，只能继续做最终归档复核、材料一致性封版、人工核验闭环或更严格的灰度前检查。Stage50 仍不能自动 approve，不能调用 xttrader，不能查询真实账户，不能真实通知。
