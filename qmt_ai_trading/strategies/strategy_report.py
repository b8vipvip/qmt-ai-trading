from __future__ import annotations
from typing import Any

def build_strategy_report(signals: list[dict[str, Any]], intents: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        'stage': 80, 'title': 'Stage80 因子候选池到 Strategy Engine dry-run TradeIntent 联调',
        'dry_run': True, 'source': 'factor_strategy_stage80',
        'signal_count': len(signals), 'trade_intent_count': len(intents), 'risk_decision_count': len(decisions),
        'blocked_count': sum(1 for d in decisions if not d.get('approved')),
        'safety': {'no_qmt_trader_api': True, 'no_live_order': True, 'no_account_query': True, 'no_auto_approve': True},
        'warnings': ['mock_data / not_live_trading 不能作为实盘依据', 'QMT Gateway 仍是唯一真实交易边界，本阶段未触达'],
    }
