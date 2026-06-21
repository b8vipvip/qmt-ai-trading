from __future__ import annotations
from .models import ReplayEvent
class ReplayBus:
    allowed={'QUOTE','BAR','TICK','SNAPSHOT','HEARTBEAT'}
    def __init__(self, gateway, speed=1.0): self.gateway=gateway; self.speed=speed; self.status='CREATED'
    def pause(self): self.status='PAUSED'
    def resume(self): self.status='RUNNING'
    def stop(self): self.status='STOPPED'
    def replay(self, symbols, timeframe='1d', limit=20):
        events=[]
        for s in symbols:
            for snap in self.gateway.get_snapshot([s]): events.append(('SNAPSHOT',snap.timestamp,s,snap.to_dict()))
            for bar in self.gateway.get_bars(s,timeframe,limit): events.append(('BAR',bar.timestamp,s,bar.to_dict()))
        events.sort(key=lambda x:(x[1],x[2],x[0]))
        out=[]
        for i,(typ,ts,s,payload) in enumerate(events[:limit],1):
            out.append(ReplayEvent(f'EVT-STAGE84-{i:04d}',typ,s,ts,payload,i).to_dict())
        self.status='RUNNING' if out else 'EMPTY'
        return out
