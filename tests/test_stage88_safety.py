from pathlib import Path

def test_stage88_safety_boundaries():
    for p in ['qmt_ai_trading/datahub/real_xtdata_loader.py','qmt_ai_trading/strategies/stage88_dry_run.py','qmt_ai_trading/risk/stage88_risk_gate.py']:
        s=Path(p).read_text(encoding='utf-8')
        assert 'XtQuantTrader' not in s
        for bad in ['query_account','query_position','query_order','query_trade','order_stock','place_order','execute_order','cancel_order']:
            assert bad not in s
        assert 'no_order_submitted' in s and 'no_account_query' in s
