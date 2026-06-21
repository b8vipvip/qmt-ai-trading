from qmt_ai_trading.market_gateway.safety import scan_obj, safety_report

def test_market_gateway_forbidden_terms_detected():
    hits=scan_obj({'note':'xttrader XtQuantTrader place_order execute_order buy_now sell_now query_account query_position query_order query_trade live_trade real_market_data real_xtdata'})
    for term in ['xttrader','XtQuantTrader','place_order','execute_order','buy_now','sell_now','query_account','query_position','query_order','query_trade','live_trade','real_market_data','real_xtdata']:
        assert term in hits

def test_market_gateway_safety_report_never_executes():
    rep=safety_report({'note':'place_order query_account'})
    assert not rep['safe'] and rep['violations']
    assert rep['sandbox'] and rep['read_only'] and rep['not_live_trading'] and rep['no_order_submitted']
