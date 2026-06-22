from .common import payload, read_json
def status(): return payload(status='READY_EMPTY', module='Data Hub', report=read_json('datahub','datahub_status.json',{}))
def symbols(): return payload(status='READY_EMPTY', symbols=read_json('datahub','datahub_symbols.json',{'symbols':[]}).get('symbols',[]))
def cache_status(): return payload(status='READY_EMPTY', cache=read_json('datahub','datahub_real_cache.json',{}))
def market_latest(): return payload(status='READY_EMPTY', market=read_json('datahub','market_latest.json',{}))
