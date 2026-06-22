from .common import payload, read_json
def context(): return payload(context=read_json('research','factor_context.json',{}))
def factors(): return payload(factors=read_json('research','factor_values.json',{}))
def candidates(): return payload(candidates=read_json('research','factor_candidates.json',[]))
