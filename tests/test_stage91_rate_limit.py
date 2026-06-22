from qmt_ai_trading.trading_gateway.account_rate_limit import AccountReadonlyRateLimiter

def test_rate_limit_blocks_fourth_query():
    rl = AccountReadonlyRateLimiter(3)
    assert rl.allow()["status"] == "PASS"
    assert rl.allow()["status"] == "PASS"
    assert rl.allow()["status"] == "PASS"
    blocked = rl.allow()
    assert blocked["status"] == "BLOCKED_BY_RATE_LIMIT"
    assert blocked["account_query_attempted"] is False
