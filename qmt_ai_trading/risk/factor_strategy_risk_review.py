from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

REQUIRED_FLAGS = {'mock_data', 'not_live_trading'}

def review_trade_intents(intents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    decisions=[]
    for intent in intents or []:
        flags=set(intent.get('risk_flags') or [])
        reasons=[]
        if not intent.get('dry_run'):
            reasons.append('TradeIntent 未标记 dry_run=True')
        if intent.get('source') != 'factor_strategy_stage80':
            reasons.append('TradeIntent source 非 Stage80 因子策略来源')
        if not REQUIRED_FLAGS <= flags:
            reasons.append('mock_data / not_live_trading 风险标记缺失')
        reasons.append('Stage80 使用 mock factor candidates，禁止作为实盘依据')
        reasons.append('未进行人工审批，禁止自动 approve')
        decisions.append({
            'intent_id': intent.get('intent_id'), 'symbol': intent.get('symbol'), 'decision': 'REJECTED_DRY_RUN',
            'approved': False, 'dry_run': True, 'risk_gate': 'factor_strategy_stage80_dry_run',
            'reasons': reasons, 'risk_flags': sorted(flags | REQUIRED_FLAGS),
            'no_order_submitted': True, 'no_account_query': True, 'no_qmt_trader_api': True, 'auto_approve': False,
            'reviewed_at': now,
        })
    return decisions
