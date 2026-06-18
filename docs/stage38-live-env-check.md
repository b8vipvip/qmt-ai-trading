# 阶段三十八：极小资金灰度只读环境核验（仍不下单）

## 阶段三十八目标
阶段三十八新增 Live Environment Check，只在本地只读核验 Python/项目文件、运行产物忽略规则、敏感文件风险、scheduler dry-run 预览、极小资金配置、白名单、Dashboard/Notification/Data Quality/Agent/Live Manual Prep/Gray Decision 等证据。

## 为什么需要极小资金灰度只读环境核验
阶段三十七已经生成人工审批准备包，但任何未来极小资金灰度前仍需要单独确认环境材料、配置边界和只读证据是否齐全。该阶段仍不启用实盘，不连接 QMT 交易接口，不调用 xttrader，不查询账户/资金/持仓/订单/成交，不真实发送通知，不下单。

## 核心模型
- `LiveEnvCheckConfig`：allowed_symbols、max_total_capital、max_single_order_value、max_symbol_weight、max_portfolio_weight、只读要求、operator/reviewer 和脱敏 metadata。
- `LiveEnvCheckItem`：单项核验，包含 check_id、scope、status、title、message、evidence、remediation 和 metadata。
- `LiveEnvCheckReport`：核验报告，包含 decision、config、checks、blocked_reasons、warnings、summary、safety_note、success 和 message。

## 决策区别
- `NOT_READY`：尚不具备环境核验材料。
- `NEED_MORE_EVIDENCE`：默认安全状态，缺少 scheduler 或证据报告等材料。
- `READY_FOR_ENV_REVIEW`：仅表示环境材料可交人工复核，不代表允许实盘。
- `BLOCKED`：发现 live flag、真实下单、真实通知、xttrader、账户查询、绕过风控或配置阻断。

## 系统文件核验
核验项目目录、核心脚本、roadmap、architecture 是否存在；缺失不崩溃，进入 WARN/FAIL。

## Git / .gitignore / sync_all.ps1 核验
核验 `.gitignore` 覆盖运行产物目录，核验 `scripts/sync_all.ps1` 存在且本阶段不修改该文件。

## 配置核验
核验 allowed_symbols 非空，max_total_capital 和 max_single_order_value 明确且保持极小资金上限，仓位比例保持保守。

## Scheduler preview 核验
核验 scheduler/register dry-run 预览不包含 `--live-enabled`、`--execute-live` 或 real-send。

## 证据核验
Dashboard、Notification Dry Run、Data Quality Tracking、Agent Research、Live Manual Prep、Gray Decision、Risk Gate / Approval / Paper / Final Acceptance 均作为本地只读证据读取。文件不存在时不崩溃，进入 NEED_MORE_EVIDENCE。

## READY_FOR_ENV_REVIEW 不代表允许实盘
`READY_FOR_ENV_REVIEW` 只代表材料可以提交人工环境复核；它不是交易授权、不是自动 GO、不是实盘开关。

## run_live_env_check.py 使用方式
```powershell
py scripts/run_live_env_check.py --output live_env_check_stage38/live_env_check.md --json-output live_env_check_stage38/live_env_check.json --allowed-symbols 510300.SH,510500.SH --max-total-capital 5000 --max-single-order-value 1000
```

## run_daily_pipeline.py --enable-live-env-check 使用方式
```powershell
py scripts/run_daily_pipeline.py --enable-live-env-check --live-env-check-output-dir live_env_check_stage38 --live-env-check-allowed-symbols 510300.SH,510500.SH --live-env-check-max-total-capital 5000 --live-env-check-max-single-order-value 1000
```

## scheduled pipeline live env check 参数说明
`run_scheduled_daily_pipeline.py` 与 `register_daily_pipeline_task.py` 支持 `--enable-live-env-check`、`--live-env-check-output-dir`、`--live-env-check-allowed-symbols`、`--live-env-check-max-total-capital`、`--live-env-check-max-single-order-value`、`--live-env-check-max-symbol-weight`、`--live-env-check-max-portfolio-weight`。

## Dashboard Live Env Check section
Dashboard 新增 Live Environment Readiness section，只读最新 Live Env Check Markdown/JSON，文件不存在时 EMPTY，不读取敏感文件，不调用外部网络，不提供下单按钮。

## 当前阶段安全边界
当前阶段不启用实盘、不调用 QMT、不调用 xttrader、不查询账户/资金/持仓/订单/成交、不真实发送通知、不下单。

## 下一阶段计划
阶段三十九：极小资金灰度最终人工授权包（仍不执行）。下一阶段把阶段三十八只读环境核验结果和全部前置材料整理为最终人工授权包，仍不下单、不调用 xttrader、不真实发送通知、不查询账户资金持仓订单成交。
