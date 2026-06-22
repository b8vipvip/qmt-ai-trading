from .xttrader_boundary import disabled_payload

def account_query_gate():
    return {**disabled_payload(), "gate":"account_query", "gate_status":"BLOCKED_BY_SAFETY", "attempt_status":"NOT_ATTEMPTED"}
