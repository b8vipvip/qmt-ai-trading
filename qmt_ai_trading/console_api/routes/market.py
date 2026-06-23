from .common import payload, read_json


def xtdata_status():
    status = read_json('market', 'xtdata_live_status.json', {})
    return payload(status=status.get('status', 'READY_EMPTY') if isinstance(status, dict) else 'READY_EMPTY', market_status=status)
