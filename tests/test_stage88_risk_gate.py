from qmt_ai_trading.risk.stage88_risk_gate import review_intents

def test_stage88_risk_gate_checks():
    d=review_intents([{'intent_id':'x','symbol':'510300.SH','quantity':100,'target_weight':.2,'dry_run':True,'no_xttrader':True}])[0]
    assert d['decision']=='APPROVED_DRY_RUN'
    assert d['checks']['t_plus_1'] and d['checks']['lot_size_100'] and d['requires_human_approval']
