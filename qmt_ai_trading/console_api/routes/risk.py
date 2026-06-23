from .common import payload, read_json


def _status(data, default='READY_EMPTY'):
    return data.get('status', default) if isinstance(data, dict) else default


def context():
    return payload(context={'module': 'Risk Gate', 'status': 'READY'})


def decisions():
    data = read_json('risk', 'risk_decisions.json', {'status': 'READY_EMPTY', 'decisions': []})
    return payload(status=_status(data), decisions=data)


def report():
    data = read_json('risk', 'risk_report.json', {'status': 'READY_EMPTY'})
    return payload(status=_status(data), report=data)
