from .common import payload, read_json
def xtdata_status(): return payload(status=read_json('market','xtdata_live_status.json',{}))
