from __future__ import annotations
from .provider_base import MarketDataProvider
from .models import MarketSymbol, MarketSnapshot, MarketBar, ReplaySession
SYMBOLS=[('510300.SH','SH','沪深300ETF'),('510500.SH','SH','中证500ETF'),('588000.SH','SH','科创50ETF')]
class MockMarketDataProvider(MarketDataProvider):
    provider_type='mock_provider'
    def list_symbols(self): return [MarketSymbol(s,e,n) for s,e,n in SYMBOLS]
    def get_snapshot(self, symbols):
        out=[]
        for i,s in enumerate(symbols):
            ex=s.split('.')[-1]; base=3.5+i*0.37
            out.append(MarketSnapshot(s,ex,'2026-01-01T09:30:00+00:00',round(base+0.03,3),base,round(base+0.08,3),round(base-0.04,3),round(base+0.02,3),1000000+i*10000,round((base+0.02)*(1000000+i*10000),2),round(base+0.01,3),round(base+0.02,3),50000,52000))
        return out
    def get_bars(self, symbol, timeframe='1d', limit=100):
        bars=[]; base=3.5+(['510300.SH','510500.SH','588000.SH'].index(symbol) if symbol in ['510300.SH','510500.SH','588000.SH'] else 0)*0.37
        for i in range(max(0,min(limit,100))):
            o=round(base+i*0.01,3); c=round(o+0.02,3)
            bars.append(MarketBar(symbol, symbol.split('.')[-1], f'2026-01-{i+1:02d}T15:00:00+00:00', o, round(c+0.03,3), round(o-0.03,3), c, 1000000+i*1000, round(c*(1000000+i*1000),2), timeframe))
        return bars
    def subscribe(self, symbols): return ReplaySession('REPLAY-STAGE84-MOCK', self.provider_type, symbols, 'SUBSCRIBED')
