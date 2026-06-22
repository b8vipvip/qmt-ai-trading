from .common import payload, read_json
def context(): return payload(context=read_json('monitoring','monitoring_input_context.json',{}))
def alerts(): return payload(alerts=read_json('monitoring','monitoring_alerts.json',{'alerts':[]}))
def circuit(): return payload(circuit_breaker=read_json('monitoring','circuit_breaker_status.json',{}))
