from .common import payload, read_json


def _status(data, default='READY_EMPTY'):
    return data.get('status', default) if isinstance(data, dict) else default


def status():
    report = read_json('paper', 'paper_trading_report.json', {})
    return payload(status=_status(report), report=report)


def orders():
    data = read_json('paper', 'paper_orders.json', {'orders': []})
    return payload(status=_status(data), orders=data.get('orders', []), report=data)


def positions():
    data = read_json('paper', 'shadow_positions.json', {'positions': []})
    return payload(status=_status(data), positions=data.get('positions', []), report=data)


def pnl():
    data = read_json('paper', 'shadow_pnl.json', {})
    return payload(status=_status(data), pnl=data.get('pnl', data), report=data)
