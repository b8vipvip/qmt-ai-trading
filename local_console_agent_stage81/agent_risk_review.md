# Stage81 Agent Risk Review

dry_run=true
not_live_trading=true
research_only=true
no_order_submitted=true
no_qmt_trader_api=true
requires_risk_gate=true
requires_human_approval=true

## Warnings
- dry_run
- fallback_used
- missing input fallback used: local_console_ai_stage78/ai_benchmark_report.json
- missing input fallback used: local_console_ai_stage78/model_usage_draft.json
- mock_data
- not_live_trading
- research_only

## Summary
Risk Agent 保留上游 Risk Gate dry-run 阻断，不允许绕过风控。