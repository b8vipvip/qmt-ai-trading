# 总体验收命令清单

## 阶段一到阶段三十一完成清单
阶段一至阶段三十一均已形成对应 `docs/stage*.md` 文档、测试和安全边界。

## 总体安全边界
当前阶段仍不实盘、不调用 QMT 交易接口、不调用 xttrader、不查询真实资金/持仓/订单/成交、不真实发送通知、不自动 approve、不自动 paper submit、不自动 live submit、不真实下单。

## pytest 验收命令
执行 `py -m compileall -q qmt_ai_trading`，然后逐项运行 `tests/test_gateway_order_safety.py` 至 `tests/test_dashboard_stage31.py` 以及 `tests/test_final_acceptance_stage32.py`。

## 全链路 smoke test
`py scripts/run_full_dry_run_smoke.py --cache-root market_data_test_stage32 --output-dir smoke_reports_stage32`

## Final Acceptance
`py scripts/run_final_acceptance.py --output final_acceptance_stage32/final_acceptance.md --json-output final_acceptance_stage32/final_acceptance.json`

## sync_all.ps1 检查
- PowerShell syntax check
- `powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode scan`
- `powershell -ExecutionPolicy Bypass -File .\scripts\sync_all.ps1 -Mode status`

## 运行产物清理
删除 `final_acceptance_stage32/ smoke_reports_stage32/ market_data_test_stage32/ dashboard_stage32/ agent_reports_stage32/ monitoring_reports_stage32/ live_gray_reports_stage32/ reports/ logs/ approvals/ paper_orders/ market_data/ data_cache/`。

## 最终声明
当前仍未实盘；后续如果进入真实小资金实盘，需要人工单独新阶段确认。
