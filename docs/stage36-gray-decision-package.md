# 阶段三十六：小资金灰度准入复核 / 人工决策包

## 阶段三十六目标
阶段三十六新增 Gray Decision Package，用于把 Risk Gate、Human Approval、Paper Trading、Live Readiness Audit、Monitoring、Data Quality Tracking、Agent Research、Live Gray Readiness、Notification Dry Run、Dashboard、Gray Rehearsal 和 Final Acceptance 等本地证据汇总为 manual-only / dry-run 人工决策包。

## 为什么需要小资金灰度准入复核 / 人工决策包
阶段三十到阶段三十五已经形成灰度前准备、只读展示、通知 dry-run 和人工流程演练。进入任何未来极小资金灰度前，仍需要单独证据包供人工复核，确认没有 CRITICAL、没有 Risk Gate bypass、没有 Human Approval bypass、没有 real-send、没有 live flag。

## 核心模型
- `GrayDecisionConfig`：记录允许标的、小资金上限、单笔上限、仓位上限、必需证据、operator/reviewer 和 manual-only metadata。
- `GrayDecisionEvidence`：记录 evidence_id、evidence_type、status、source_path、summary、severity、blocked_reason 和脱敏 metadata。
- `GrayDecisionPackage`：记录 package_id、created_at、decision、config、evidence、checklist、blocked_reasons、warnings、manual signature placeholder、summary、safety_note 和 metadata。

## 决策区别
- `NOT_ELIGIBLE`：证据或配置不具备准入讨论条件。
- `NEED_MORE_EVIDENCE`：默认安全状态，缺少证据或存在 WARN，需要继续补充材料。
- `READY_FOR_MANUAL_DECISION`：所有必需证据 PRESENT 且无 blocker，只代表可以进入人工讨论。
- `BLOCKED`：出现 live flag、真实通知、下单、账户查询、Risk bypass、CRITICAL 或 Circuit Breaker OPEN 等阻断项。

## 必需证据说明
- Risk Gate：必须存在且无 bypass。
- Human Approval：必须存在且明确，不允许自动 approve。
- Paper Trading：必须 dry-run/local only。
- Live Readiness Audit：不得有 critical failure。
- Monitoring：不得有 CRITICAL alerts，Circuit Breaker 不得 OPEN。
- Data Quality Tracking：必须足以人工复核，FAIL/UNKNOWN 不能 READY。
- Agent Research：只读，不调用外部网络或交易接口。
- Live Gray Readiness：不得 auto-GO，NO_GO/BLOCKED 只能作为阻断或补证证据。
- Notification Dry Run：不得 real-send，不调用 SMTP / Telegram API / 企业微信 API。
- Dashboard：只读，无 order entry。
- Gray Rehearsal：必须完成，WARN 进入 NEED_MORE_EVIDENCE。
- Final Acceptance：作为最终运行手册 / 总体验收证据。

## CLI 使用方式
```powershell
py scripts/run_gray_decision_package.py --output gray_decision_stage36/gray_decision_package.md --json-output gray_decision_stage36/gray_decision_package.json --allowed-symbols 510300.SH,510500.SH --max-total-capital 5000 --max-single-order-value 1000
```

## Daily Pipeline 使用方式
```powershell
py scripts/run_daily_pipeline.py --enable-gray-decision-package --gray-decision-output-dir gray_decision_stage36 --gray-decision-allowed-symbols 510300.SH,510500.SH --gray-decision-max-total-capital 5000 --gray-decision-max-single-order-value 1000
```

## Scheduled pipeline 参数说明
`run_scheduled_daily_pipeline.py` 和 `register_daily_pipeline_task.py` 支持 `--enable-gray-decision-package`、`--gray-decision-output-dir`、`--gray-decision-allowed-symbols`、`--gray-decision-max-total-capital`、`--gray-decision-max-single-order-value`、`--gray-decision-max-symbol-weight`、`--gray-decision-max-portfolio-weight`。计划任务默认不包含 `--live-enabled` 或 real-send 参数。

## Dashboard Gray Decision Package section
Dashboard 新增只读 Gray Decision Package section，只读取本地 Markdown / JSON，文件不存在时 EMPTY，不读取敏感文件，不调用外部网络，不提供下单按钮。

## 安全边界
READY_FOR_MANUAL_DECISION 不代表允许实盘，不代表交易授权，不代表自动 GO。当前阶段不启用实盘、不调用 QMT、不调用 xttrader、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单。

## 下一阶段计划
阶段三十七：极小资金灰度实盘人工审批准备（仍默认关闭）。阶段三十七仍默认关闭实盘，不真实下单，不调用 xttrader，不真实发送通知。
