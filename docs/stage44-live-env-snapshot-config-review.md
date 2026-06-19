# 阶段四十四：灰度前配置封存复核与只读环境快照

Stage44 在 Stage43 人工签字清单与配置封存摘要基础上，生成配置封存复核报告和只读环境快照，用于未来人工会议确认当前运行环境、配置边界、忽略规则、安全开关和只读产物是否满足灰度前检查要求。

## 安全边界

- Stage44 不等于实盘授权。
- Stage44 不调用 xttrader。
- Stage44 不调用 QMT 交易接口。
- Stage44 不真实下单。
- Stage44 不查询资金、持仓、订单、成交。
- Stage44 不真实发送通知。
- Stage44 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_ENV_SNAPSHOT` 只表示环境快照材料可供人工复核，不代表可以实盘。

## 只读输入

默认只读取本地 Markdown / JSON / `.gitignore` 材料，包括 Stage40 red-line review、Stage41 ledger、Stage42 human review、Stage43 signature/freeze package 与 validation log 目录状态。缺失证据仅记录 WARN / SKIPPED，不崩溃。

## 输出材料

默认输出目录为 `live_env_snapshot_stage44/`，运行产物不提交：

- `live_env_snapshot.md`
- `live_env_snapshot.json`
- `readonly_environment_snapshot.md`
- `readonly_environment_snapshot.json`

## 决策语义

- `NO_GO`：存在 CRITICAL 或明确阻断，例如 Stage40/Stage41 BLOCKED、Stage42/Stage43 NO_GO 或 critical > 0。
- `NEED_MORE_EVIDENCE`：缺少证据但没有 CRITICAL；Stage43 `NEED_MORE_EVIDENCE` 且 critical=0 时，Stage44 仍可生成材料并保持该状态。
- `READY_FOR_ENV_SNAPSHOT`：只表示环境快照材料可供人工复核；不是实盘授权。

## 验收摘要

Stage44 新增 `qmt_ai_trading/live_env_snapshot/`、`scripts/run_live_env_snapshot.py`、`scripts/validate_stage44.ps1` 和测试 `tests/test_live_env_snapshot_stage44.py`。Daily / Scheduled pipeline 仅通过可选参数生成只读环境快照材料，默认不启用；注册任务脚本仍然只 preview，不注册真实任务。

## Stage45 预告

Stage45 建议名称为“阶段四十五：灰度前只读运行手册与人工流程演练”。Stage45 仍不能直接实盘，只能继续做灰度前只读运行手册、人工确认流程演练、异常处理手册和 go/no-go 会议材料；仍不能自动 approve，不能调用 xttrader，不能查询真实账户，不能真实通知。
