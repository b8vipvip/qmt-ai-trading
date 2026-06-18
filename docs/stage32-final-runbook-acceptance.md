# 阶段三十二：运行手册 / 部署手册 / 总体验收

## 阶段三十二目标
整理本地运行、数据缓存、Daily Pipeline、Scheduler、Approval、Paper、Monitoring、Agent、Live Gray、Dashboard 全链路手册，并提供 Final Acceptance 与 Full Dry Run Smoke。

## 为什么需要
运行手册和验收层把各阶段证据统一为可复查文档，降低误操作风险，明确当前系统仍处 dry-run / shadow / paper only。

## 模型
- `AcceptanceDecision`：`PASS`、`WARN`、`FAIL`。
- `AcceptanceCheck`：记录单项检查、证据、修复建议和 metadata。
- `AcceptanceReport`：汇总决策、检查、summary、safety note 和 metadata。

## run_final_acceptance.py
`py scripts/run_final_acceptance.py --output final_acceptance_stage32/final_acceptance.md --json-output final_acceptance_stage32/final_acceptance.json`

## run_full_dry_run_smoke.py
`py scripts/run_full_dry_run_smoke.py --cache-root market_data_test_stage32 --output-dir smoke_reports_stage32`

## 最终安全边界
当前阶段仍不实盘、不调用 QMT 交易接口、不调用 xttrader、不查询真实资金/持仓/订单/成交、不真实发送通知、不自动 approve、不自动 paper submit、不自动 live submit、不真实下单。

## 后续增强建议
项目总体验收完成 / 后续增强待定。建议仅在新的人工确认阶段继续：真实 QMT 数据质量长期追踪、真实通知接入、小资金灰度实盘人工流程、UI 交互增强、多策略组合等。
