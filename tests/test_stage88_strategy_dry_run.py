from qmt_ai_trading.strategies.stage88_dry_run import build_strategy, WHITELIST

def test_stage88_strategy_dry_run():
    sig,intents=build_strategy([{'symbol':'510300.SH','rank':1,'composite_score':1,'risk_flags':[]},{'symbol':'BAD','rank':1,'composite_score':9,'risk_flags':[]}])
    assert sig and all(s['symbol'] in WHITELIST and s['dry_run'] and s['target_weight'] <= .25 for s in sig)
    assert all(i['no_order_submitted'] and i['quantity'] % 100 == 0 for i in intents)
