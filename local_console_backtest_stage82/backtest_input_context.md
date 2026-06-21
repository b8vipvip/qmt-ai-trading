# Backtest Input Context

dry_run=true
not_live_trading=true
research_only=true
fallback_used=true
mock_data=true

该结果仅用于前端联调和研究展示，不能作为实盘依据。

```json
{
  "stage": "Stage82",
  "input_source": "stage81",
  "input_files": {
    "agent_research_report": "local_console_agent_stage81/agent_research_report.json",
    "agent_debate": "local_console_agent_stage81/agent_debate.json",
    "agent_risk_review": "local_console_agent_stage81/agent_risk_review.json",
    "agent_portfolio_review": "local_console_agent_stage81/agent_portfolio_review.json",
    "frontend_agent_contract": "local_console_agent_stage81/frontend_agent_contract.json",
    "factor_strategy_report": "local_console_strategy_stage80/factor_strategy_report.json",
    "factor_trade_intents": "local_console_strategy_stage80/factor_trade_intents.json",
    "factor_risk_decisions": "local_console_strategy_stage80/factor_risk_decisions.json",
    "factor_candidates": "local_console_factor_stage79/factor_candidates.json"
  },
  "warnings": [
    "missing input fallback used: local_console_strategy_stage80/factor_strategy_report.json",
    "missing input fallback used: local_console_strategy_stage80/factor_trade_intents.json",
    "missing input fallback used: local_console_strategy_stage80/factor_risk_decisions.json",
    "missing input fallback used: local_console_factor_stage79/factor_candidates.json"
  ],
  "fallback_used": true,
  "mock_data": true,
  "data_quality": "fallback_safe",
  "linked_symbols": [
    "510300.SH"
  ],
  "dry_run": true,
  "not_live_trading": true,
  "research_only": true,
  "no_order_submitted": true,
  "no_qmt_trader_api": true,
  "requires_risk_gate": true,
  "requires_human_approval": true,
  "backtest_mode": "mock_shadow",
  "disclaimer": "该结果仅用于前端联调和研究展示，不能作为实盘依据。",
  "unsafe": false,
  "forbidden_terms": []
}
```
