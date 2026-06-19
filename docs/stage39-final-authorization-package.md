# 阶段三十九：极小资金灰度最终人工授权包（仍不执行）

## 阶段三十九目标
阶段三十九新增 Final Authorization Package，把 Live Env Check、Live Manual Prep、Gray Decision Package、Gray Rehearsal、Live Gray Readiness、Live Readiness Audit、Risk Gate、Human Approval、Paper Trading、Monitoring、Data Quality Tracking、Agent Research、Notification Dry Run、Dashboard 和 Final Acceptance 证据汇总为最终人工审阅材料包。

## 为什么需要极小资金灰度最终人工授权包
阶段三十八已完成只读环境核验，但进入任何未来极小资金灰度前仍需要独立的人工会议/签字材料。本包只整理证据、Checklist、禁止事项、残余风险、未来阶段进入条件和签字占位，不开启实盘、不自动 GO。

## 核心模型
- `FinalAuthorizationConfig`：allowed_symbols、max_total_capital、max_single_order_value、max_symbol_weight、max_portfolio_weight、必需证据开关和人工签字角色。
- `FinalAuthorizationEvidence`：evidence_id、evidence_type、status、source_path、summary、severity、blocked_reason 和脱敏 metadata。
- `FinalAuthorizationPackage`：package_id、created_at、decision、config、evidence、checklist、forbidden_items、residual_risks、future_stage_requirements、signoff_placeholders、blocked_reasons、warnings、summary、safety_note。

## 决策区别
- `NOT_AUTHORIZED`：当前材料不是交易授权。
- `NEED_MORE_EVIDENCE`：默认安全状态，缺少必需证据或存在 warning。
- `READY_FOR_FINAL_SIGNOFF_REVIEW`：仅表示材料可以交人工最终签字审阅，不代表允许实盘。
- `BLOCKED`：发现 live flag、真实下单、真实通知、xttrader、账户/资金/持仓/订单/成交查询、绕过风控、CRITICAL 或 Circuit Breaker OPEN。

## 必需证据说明
必需证据覆盖 Live Env Check、Live Manual Prep、Gray Decision Package、Gray Rehearsal、Live Gray Readiness、Live Readiness Audit、Risk Gate、Human Approval、Paper Trading、Monitoring、Data Quality Tracking、Agent Research、Notification Dry Run、Dashboard、Final Acceptance。缺失文件不崩溃，但进入 `NEED_MORE_EVIDENCE`。

## 禁止事项确认页
禁止自动开启 live、自动审批、自动 paper submit、自动 live submit、真实通知发送、调用 xttrader、调用 QMT 交易 API、查询账户/资金/持仓/订单/成交、提交订单、绕过 Risk Gate 或 Human Approval、隐藏 live flag、把本包当作交易授权。

## 残余风险确认页
数据质量可能仍不完整；paper trading 与真实执行可能不同；滑点和流动性风险仍存在；操作错误、QMT 环境差异、人工审批错误、网络/客户端/券商行为差异和策略失效风险仍存在。

## 未来单独阶段进入条件
新阶段必须单独人工确认，仍默认关闭实盘，并再次确认 QMT 环境、Risk Gate、Human Approval、Paper Trading、Live Readiness Audit、Monitoring / Circuit Breaker、Notification dry-run 状态、allowed_symbols 和 capital limits。不得直接从本包自动执行交易。

## 人工签字占位
包含 Operator signature、Reviewer signature、Risk owner signature、Final approver signature、Date、Final manual decision 和 “This signature still does not submit orders.”。

## run_final_authorization_package.py 使用方式
```powershell
py scripts/run_final_authorization_package.py --output final_authorization_stage39/final_authorization.md --json-output final_authorization_stage39/final_authorization.json --allowed-symbols 510300.SH,510500.SH --max-total-capital 5000 --max-single-order-value 1000
```

## run_daily_pipeline.py --enable-final-authorization-package 使用方式
```powershell
py scripts/run_daily_pipeline.py --enable-final-authorization-package --final-authorization-output-dir final_authorization_stage39 --final-authorization-allowed-symbols 510300.SH,510500.SH --final-authorization-max-total-capital 5000 --final-authorization-max-single-order-value 1000
```

## scheduled pipeline final authorization 参数说明
`run_scheduled_daily_pipeline.py` 与 `register_daily_pipeline_task.py` 支持 `--enable-final-authorization-package`、`--final-authorization-output-dir`、`--final-authorization-allowed-symbols`、`--final-authorization-max-total-capital`、`--final-authorization-max-single-order-value` 等参数。默认不包含 `--live-enabled`、`--execute-live` 或 real-send 参数。

## Dashboard Final Authorization Package section
Dashboard 新增 Final Authorization Package section，只读最新 Markdown / JSON。文件不存在时 EMPTY，不读取敏感文件，不调用外部网络，不提供下单按钮。

## READY_FOR_FINAL_SIGNOFF_REVIEW 不代表允许实盘
`READY_FOR_FINAL_SIGNOFF_REVIEW` 只代表材料可以提交人工最终签字审阅，不代表交易授权、不代表自动 GO、不启用 live、不提交订单。

## 当前阶段安全边界
当前阶段不启用实盘、不调用 QMT、不调用 xttrader、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单。

## 下一阶段计划
阶段四十：实盘开关隔离与最终红线复核（仍默认关闭）。阶段四十仍不执行实盘，不下单、不调用 xttrader、不真实发送通知、不查询账户资金持仓订单成交。
