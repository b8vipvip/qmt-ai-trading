# 阶段四十二：灰度前人工复核包与只读演练封版

Stage42 在 Stage41 只读台账基础上，生成灰度前人工复核包与只读演练封版材料，用于未来人工 go/no-go 会议或本地复核。

## 安全边界

- Stage42 不等于实盘授权。
- Stage42 不调用 xttrader。
- Stage42 不真实下单。
- Stage42 不查询资金、持仓、订单、成交。
- Stage42 不真实发送通知。
- Stage42 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_HUMAN_REVIEW` 只表示材料可供人工复核，不代表可以实盘。

## 输出材料

默认输出目录为 `live_gray_review_stage42/`，运行产物不提交：

- `live_gray_review.md`
- `live_gray_review.json`
- `readonly_rehearsal.md`
- `readonly_rehearsal.json`

## 决策语义

- `NO_GO`：存在 critical 或明确阻断，例如 Stage40/Stage41 BLOCKED 或 critical > 0。
- `NEED_MORE_EVIDENCE`：缺少证据但没有 critical，可继续生成复核包。
- `READY_FOR_HUMAN_REVIEW`：材料可供人工复核，但仍不是实盘授权。

## 验收摘要

Stage42 新增 `qmt_ai_trading/live_gray_review/`、`scripts/run_live_gray_review.py`、`scripts/validate_stage42.ps1` 和测试 `tests/test_live_gray_review_stage42.py`。Daily / Scheduled pipeline 仅通过可选参数生成只读复核材料，默认不启用，不注册真实任务。

## Stage43 预告

Stage43 仍不得直接实盘；只能继续做人工签字、只读演练、配置封存或更严格的灰度前检查。
