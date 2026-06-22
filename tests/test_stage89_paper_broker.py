from qmt_ai_trading.paper_trading.paper_broker import PaperBroker

def test_paper_broker_fills_allowed_order():
    b=PaperBroker(); o=b.submit_paper_order({'intent_id':'i1','symbol':'510300.SH','side':'buy','quantity':100},{'decision':'APPROVED_DRY_RUN','reasons':['ok']}); f=b.simulate_fill(o,{'symbols':{'510300.SH':{'bars':[{'close':3.5}]}}})
    assert o.paper_order and f.fill_status=='FILLED' and f.simulated_fill_price==3.5

def test_paper_broker_rejects_risk_denied_order():
    b=PaperBroker(); o=b.submit_paper_order({'intent_id':'i2','symbol':'510300.SH','side':'buy','quantity':100},{'decision':'REJECTED','reasons':['blocked']}); f=b.simulate_fill(o,{})
    assert o.fill_status=='REJECTED' and f.quantity==0
