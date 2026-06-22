from .common import payload, read_json
def context(): return payload(context={'module':'Risk Gate','status':'READY_EMPTY'})
def decisions(): return payload(decisions=read_json('risk','risk_decisions.json',[]))
def report(): return payload(report=read_json('risk','risk_report.json',{}))
