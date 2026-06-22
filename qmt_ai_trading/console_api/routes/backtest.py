from .common import payload, read_json
def shadow_replay(): return payload(shadow_replay=read_json('backtest','shadow_replay_result.json',{}))
