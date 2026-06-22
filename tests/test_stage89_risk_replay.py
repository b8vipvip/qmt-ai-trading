from qmt_ai_trading.paper_trading.paper_broker import PaperBroker
from qmt_ai_trading.paper_trading.risk_replay import replay

def test_risk_replay_flags_bypass():
    b=PaperBroker(); o=b.submit_paper_order({'intent_id':'i','symbol':'s','quantity':1},{'decision':'REJECTED','reasons':['no']}); o.fill_status='FILLED'
    assert replay([o])[0].safety_violation is True
