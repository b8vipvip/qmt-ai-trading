from __future__ import annotations
from .mock_provider import MockMarketDataProvider
from .recorded_provider import RecordedMarketDataProvider
class SandboxMarketDataGateway:
    def __init__(self, provider=None, provider_type='mock_provider'):
        self.provider=provider or (RecordedMarketDataProvider() if provider_type=='recorded_provider' else MockMarketDataProvider())
        self.provider_type=self.provider.provider_type
    def list_symbols(self): return self.provider.list_symbols()
    def get_snapshot(self, symbols): return self.provider.get_snapshot(symbols)
    def get_bars(self, symbol, timeframe='1d', limit=100): return self.provider.get_bars(symbol,timeframe,limit)
    def subscribe(self, symbols): return self.provider.subscribe(symbols)
