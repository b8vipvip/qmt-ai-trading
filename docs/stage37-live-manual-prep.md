# 阶段三十七：极小资金灰度实盘人工审批准备（仍默认关闭）

## 阶段目标
阶段三十七新增 Live Manual Approval Prep，用于在 Gray Decision Package 之后生成极小资金灰度实盘的人工审批准备包。该包只汇总证据、配置检查、禁止事项、残余风险和人工签字占位，不启用实盘。

## 为什么需要
阶段三十六只给出小资金灰度准入复核材料；阶段三十七进一步把极小资金范围、白名单、单笔金额上限、最大仓位上限、只读证据和人工签字页整理为最终人工审阅材料，为后续独立阶段的只读环境核验做准备。

## 核心模型
- `LiveManualPrepConfig`：保存 allowed_symbols、max_total_capital、max_single_order_value、max_symbol_weight、max_portfolio_weight、证据要求和 operator/reviewer/risk owner。
- `LiveManualPrepEvidence`：保存 evidence_id、evidence_type、status、source_path、summary、severity、blocked_reason 和脱敏 metadata。
- `LiveManualPrepPackage`：保存 package_id、created_at、decision、config、evidence、checklist、forbidden_items、residual_risks、signoff_placeholders、blocked_reasons、warnings、summary、safety_note 和 metadata。

## 决策区别
- `NOT_READY`：材料不足，尚不能形成签字审阅包。
- `NEED_MORE_EVIDENCE`：默认安全状态，缺少必需证据或存在 warning。
- `READY_FOR_SIGNOFF`：仅表示可交给人工审阅签字，不代表允许实盘。
- `BLOCKED`：发现 live flag、真实下单、真实通知、xttrader、账户/资金/持仓/订单/成交查询、绕过风控、CRITICAL 或 Circuit Breaker OPEN 等阻断项。

## 必需证据说明
证据包括 Gray Decision Package、Live Gray Readiness、Gray Rehearsal、Live Readiness Audit、Risk Gate、Human Approval、Paper Trading、Monitoring / Circuit Breaker、Data Quality Tracking、Agent Research、Notification Dry Run、Dashboard 和 Final Acceptance。

## 禁止事项确认页
禁止自动开启 live、自动审批、自动 paper submit、自动 live submit、真实通知发送、调用 xttrader、调用 QMT 交易 API、查询账户/资金/持仓/订单/成交、提交订单、绕过 Risk Gate 或 Human Approval。

## 残余风险确认页
数据质量、paper 与真实执行差异、滑点流动性、操作错误、QMT 环境差异和人工审批错误仍可能存在。

## 人工签字占位
包内包含 Operator signature、Reviewer signature、Risk owner signature、Date、Final manual decision，以及 “This signature still does not submit orders.” 明确声明。

## CLI 使用方式
```powershell
py scripts/run_live_manual_prep.py --output live_manual_prep_stage37/live_manual_prep.md --json-output live_manual_prep_stage37/live_manual_prep.json --allowed-symbols 510300.SH,510500.SH --max-total-capital 5000 --max-single-order-value 1000
```

## Daily Pipeline 使用方式
```powershell
py scripts/run_daily_pipeline.py --enable-live-manual-prep --live-manual-prep-output-dir live_manual_prep_stage37 --live-manual-prep-allowed-symbols 510300.SH,510500.SH --live-manual-prep-max-total-capital 5000 --live-manual-prep-max-single-order-value 1000
```

## Scheduled pipeline 参数
`run_scheduled_daily_pipeline.py` 与 `register_daily_pipeline_task.py` 支持 `--enable-live-manual-prep`、`--live-manual-prep-output-dir`、`--live-manual-prep-allowed-symbols`、`--live-manual-prep-max-total-capital`、`--live-manual-prep-max-single-order-value`、`--live-manual-prep-max-symbol-weight`、`--live-manual-prep-max-portfolio-weight`。

## Dashboard section
Dashboard 新增 Live Manual Prep section，只读最新 Markdown / JSON。文件不存在时 EMPTY，不读取敏感文件，不调用外部网络，不提供下单按钮。

## 安全边界
READY_FOR_SIGNOFF 不代表允许实盘，不代表交易授权，不代表自动 GO。当前阶段不启用实盘、不调用 QMT、不调用 xttrader、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单。

## 下一阶段计划
阶段三十八：极小资金灰度只读环境核验（仍不下单）。阶段三十八仍不启用真实实盘，不真实下单，不调用 xttrader，不真实发送通知。
