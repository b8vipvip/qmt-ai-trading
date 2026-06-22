from .xttrader_boundary import disabled_payload

def order_submit_gate():
    return {**disabled_payload(), "gate":"order_submit", "gate_status":"BLOCKED_BY_SAFETY", "attempt_status":"NOT_ATTEMPTED", "order_submit_blocked": True}
