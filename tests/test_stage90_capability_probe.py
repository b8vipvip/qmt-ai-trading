from qmt_ai_trading.trading_gateway.capability_probe import run_capability_probe

def test_probe_disabled():
    p = run_capability_probe()
    assert p["status"] == "DISABLED"
    for k in ["import_probe", "account_query_probe", "order_submit_probe"]:
        assert p[k]["block_status"] == "BLOCKED_BY_SAFETY"
        assert p[k]["attempt_status"] == "NOT_ATTEMPTED"
        assert p[k]["real_order_submitted"] is False
