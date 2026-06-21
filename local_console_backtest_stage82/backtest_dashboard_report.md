# Backtest Dashboard Report

dry_run=true
not_live_trading=true
research_only=true
fallback_used=true
mock_data=true

该结果仅用于前端联调和研究展示，不能作为实盘依据。

```json
{
  "stage": "Stage82",
  "created_at": "2026-06-21T12:43:59.185992+00:00",
  "summary": "回测分析与 Agent 研究报告联动看板 dry-run 已完成；不生成订单。",
  "output_dir": "local_console_backtest_stage82",
  "report_path": "local_console_backtest_stage82/backtest_dashboard_report.md",
  "context": {
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
  },
  "shadow_replay_result": {
    "stage": "Stage82",
    "backtest_mode": "mock_shadow",
    "shadow_replay": [
      {
        "symbol": "510300.SH",
        "shadow_trade_id": "shadow-1",
        "signal": "WATCH_ONLY",
        "mock_return": 0.012,
        "max_drawdown": 0.025,
        "win": true,
        "holding_days": 5,
        "linked_trade_intent": "mock-intent-1",
        "dry_run": true,
        "not_live_trading": true,
        "research_only": true
      }
    ],
    "trade_count": 1,
    "data_quality": "fallback_safe",
    "dry_run": true,
    "not_live_trading": true,
    "research_only": true,
    "no_order_submitted": true,
    "no_qmt_trader_api": true,
    "requires_risk_gate": true,
    "requires_human_approval": true,
    "fallback_used": true,
    "mock_data": true,
    "disclaimer": "该结果仅用于前端联调和研究展示，不能作为实盘依据。",
    "unsafe": false,
    "forbidden_terms": []
  },
  "performance_metrics": {
    "total_return": 0.012,
    "annualized_return": 0.144,
    "max_drawdown": 0.025,
    "volatility": 0.0,
    "sharpe_like": 1.2,
    "win_rate": 1.0,
    "trade_count": 1,
    "turnover": 0.1,
    "avg_holding_days": 5.0,
    "risk_rejected_count": 0,
    "approved_dry_run_count": 0,
    "data_quality": "fallback_safe",
    "dry_run": true,
    "not_live_trading": true,
    "research_only": true,
    "no_order_submitted": true,
    "no_qmt_trader_api": true,
    "requires_risk_gate": true,
    "requires_human_approval": true,
    "fallback_used": true,
    "mock_data": true,
    "backtest_mode": "mock_shadow",
    "disclaimer": "该结果仅用于前端联调和研究展示，不能作为实盘依据。",
    "unsafe": false,
    "forbidden_terms": []
  },
  "performance_attribution": {
    "performance_attribution": [
      {
        "symbol": "510300.SH",
        "return_contribution": 0.012,
        "drawdown_contribution": 0.025,
        "factor_link": "Stage79 candidate",
        "risk_note": "watch only; not executable"
      }
    ],
    "top_contributors": [
      {
        "symbol": "510300.SH",
        "return_contribution": 0.012,
        "drawdown_contribution": 0.025,
        "factor_link": "Stage79 candidate",
        "risk_note": "watch only; not executable"
      }
    ],
    "risk_contributors": [
      {
        "symbol": "510300.SH",
        "return_contribution": 0.012,
        "drawdown_contribution": 0.025,
        "factor_link": "Stage79 candidate",
        "risk_note": "watch only; not executable"
      }
    ],
    "portfolio_summary": {
      "total_return": 0.012,
      "max_drawdown": 0.025,
      "sharpe_like": 1.2
    },
    "dry_run": true,
    "not_live_trading": true,
    "research_only": true,
    "no_order_submitted": true,
    "no_qmt_trader_api": true,
    "requires_risk_gate": true,
    "requires_human_approval": true,
    "fallback_used": true,
    "mock_data": true,
    "backtest_mode": "mock_shadow",
    "disclaimer": "该结果仅用于前端联调和研究展示，不能作为实盘依据。",
    "unsafe": false,
    "forbidden_terms": []
  },
  "agent_backtest_comparison": {
    "agent_backtest_comparison": [
      {
        "agent_id": "fallback_agent",
        "agent_name": "Fallback Research Agent",
        "recommendation_type": "RESEARCH_ONLY",
        "confidence": 0.5,
        "risk_flags": [
          "fallback_used",
          "mock_data"
        ],
        "linked_symbols": [
          "510300.SH"
        ],
        "linked_trade_intents": [],
        "backtest_summary": {
          "total_return": 0.012,
          "max_drawdown": 0.025,
          "win_rate": 1.0
        },
        "agreement_score": 0.55,
        "disagreement_points": [
          "agreement_score is research-only, not a trade signal",
          "mock/fallback data cannot support live decisions"
        ],
        "risk_consistency": "consistent_with_risk_gate",
        "limitations": [
          "missing agent outputs",
          "该结果仅用于前端联调和研究展示，不能作为实盘依据。"
        ],
        "research_only": true,
        "dry_run": true,
        "not_live_trading": true
      }
    ],
    "comparison_logic": [
      "Agent 看多观点 vs 回测收益",
      "Risk Agent 观点 vs RiskDecision 阻断原因",
      "Portfolio Manager 观点 vs 组合风险收益"
    ],
    "dry_run": true,
    "not_live_trading": true,
    "research_only": true,
    "no_order_submitted": true,
    "no_qmt_trader_api": true,
    "requires_risk_gate": true,
    "requires_human_approval": true,
    "fallback_used": true,
    "mock_data": true,
    "backtest_mode": "mock_shadow",
    "disclaimer": "该结果仅用于前端联调和研究展示，不能作为实盘依据。",
    "unsafe": false,
    "forbidden_terms": []
  },
  "warnings": [
    "missing input fallback used: local_console_strategy_stage80/factor_strategy_report.json",
    "missing input fallback used: local_console_strategy_stage80/factor_trade_intents.json",
    "missing input fallback used: local_console_strategy_stage80/factor_risk_decisions.json",
    "missing input fallback used: local_console_factor_stage79/factor_candidates.json"
  ],
  "dry_run": true,
  "not_live_trading": true,
  "research_only": true,
  "no_order_submitted": true,
  "no_qmt_trader_api": true,
  "requires_risk_gate": true,
  "requires_human_approval": true,
  "fallback_used": true,
  "mock_data": true,
  "backtest_mode": "mock_shadow",
  "disclaimer": "该结果仅用于前端联调和研究展示，不能作为实盘依据。",
  "unsafe": false,
  "forbidden_terms": []
}
```
