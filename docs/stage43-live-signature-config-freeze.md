# 阶段四十三：灰度前人工签字清单与配置封存

Stage43 在 Stage42 灰度前人工复核包基础上，生成灰度前人工签字清单与配置封存摘要，用于未来人工会议、配置冻结复核和下一阶段只读环境快照准备。

## 安全边界

- Stage43 不等于实盘授权。
- Stage43 不调用 xttrader。
- Stage43 不调用 QMT 交易接口。
- Stage43 不真实下单。
- Stage43 不查询资金、持仓、订单、成交。
- Stage43 不真实发送通知。
- Stage43 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_SIGNATURE` 只表示材料可供人工签字复核，不代表可以实盘。

## 只读输入

默认读取以下本地材料，缺失时只记录 WARN / SKIPPED，不崩溃：

- `live_gray_review_stage42/live_gray_review.json`
- `live_gray_review_stage42/live_gray_review.md`
- `live_gray_review_stage42/readonly_rehearsal.json`
- `live_gray_review_stage42/readonly_rehearsal.md`
- `live_gray_ledger_stage41/live_gray_ledger.json`
- `redline_review_stage40/redline_review.json`
- `validation_logs/` 仅作为本地运行产物检查，不提交。

## 输出材料

默认输出目录为 `live_signature_freeze_stage43/`，运行产物不提交：

- `live_signature_freeze.md`
- `live_signature_freeze.json`
- `config_freeze.md`
- `config_freeze.json`

## 决策语义

- `NO_GO`：存在 CRITICAL 或明确阻断，例如 Stage40/Stage41 BLOCKED、Stage42 NO_GO 或 critical > 0。
- `NEED_MORE_EVIDENCE`：缺少证据但没有 CRITICAL；Stage42 `NEED_MORE_EVIDENCE` 且 critical=0 时，Stage43 仍可生成材料并保持该状态。
- `READY_FOR_SIGNATURE`：材料可供人工签字复核；不是实盘授权。

## 验收摘要

Stage43 新增 `qmt_ai_trading/live_signature_freeze/`、`scripts/run_live_signature_freeze.py`、`scripts/validate_stage43.ps1` 和测试 `tests/test_live_signature_freeze_stage43.py`。Daily / Scheduled pipeline 仅通过可选参数生成只读签字与配置封存材料，默认不启用；注册任务脚本仍然只 preview，不注册真实任务。

## Stage44 预告

Stage44 建议名称为“阶段四十四：灰度前只读环境快照与最终冻结核验”。Stage44 仍不能直接实盘，只能继续做配置封存复核、人工签字校验、只读环境快照或更严格的灰度前检查；仍不能自动 approve，不能调用 xttrader，不能查询真实账户，不能真实通知。
