from __future__ import annotations
from .mock_provider import MockMarketDataProvider
class RecordedMarketDataProvider(MockMarketDataProvider):
    provider_type='recorded_provider'
