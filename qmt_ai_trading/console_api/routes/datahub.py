from .common import payload, read_json


def _status(data, default='READY_EMPTY'):
    return data.get('status', default) if isinstance(data, dict) else default


def status():
    report = read_json('datahub', 'datahub_status.json', {})
    return payload(status=_status(report), module='Data Hub', report=report)


def symbols():
    data = read_json('datahub', 'datahub_symbols.json', {'symbols': []})
    return payload(status=_status(data), symbols=data.get('symbols', []), report=data)


def cache_status():
    cache = read_json('datahub', 'datahub_real_cache.json', {})
    return payload(status=_status(cache), cache=cache)


def market_latest():
    market = read_json('datahub', 'market_latest.json', {})
    return payload(status=_status(market), market=market)
