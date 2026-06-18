# Monitoring / Agent / Dashboard 操作手册

## Monitoring
`py scripts/run_monitoring_check.py --output monitoring_reports_stage32/monitoring.md --json-output monitoring_reports_stage32/monitoring.json --dry-run-alerts`
Dry-run alert 只写本地报告，不真实发送通知。Circuit Breaker：`OPEN` 暂停自动化动作建议，`HALF_OPEN` 人工观察，`CLOSED` 正常观察。

## Agent Research
`py scripts/run_agent_research.py --output agent_reports_stage32/agent_research.md --json-output agent_reports_stage32/agent_research.json --mode local_rules --include-monitoring --include-backtest --include-human-checklist`
Agent Research 只读，不调用外部 LLM，不审批、不下单。

## Dashboard
`py scripts/build_dashboard.py --output dashboard_stage32/index.html --report-dir reports --monitoring-dir monitoring_reports_stage32 --agent-dir agent_reports_stage32 --live-gray-dir live_gray_reports_stage32`
`py scripts/run_dashboard_preview.py --dashboard dashboard_stage32/index.html --print-path-only`
Dashboard 只读，不提供下单按钮。

当前阶段仍不实盘、不调用 QMT 交易接口、不调用 xttrader、不查询真实资金/持仓/订单/成交、不真实发送通知、不自动 approve、不自动 paper submit、不自动 live submit、不真实下单。
