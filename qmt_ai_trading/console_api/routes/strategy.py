from .common import payload, read_json
def context(): return payload(context={'module':'Strategy','status':'READY_EMPTY'})
def signals(): return payload(signals=read_json('strategy','strategy_signals.json',[]))
def intents(): return payload(trade_intents=read_json('strategy','trade_intents.json',[]))
