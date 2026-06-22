from .common import payload, read_json
def context(): return payload(context=read_json('agent','agent_context.json',{}))
def report(): return payload(report=read_json('agent','agent_research_report.json',{}))
