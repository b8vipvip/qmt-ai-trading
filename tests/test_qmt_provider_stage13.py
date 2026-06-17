from __future__ import annotations

from pathlib import Path

from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.datahub.market_data import get_historical_bars_cached
from qmt_ai_trading.datahub.providers import MockHistoricalDataProvider, create_historical_provider, fetch_historical_bars
from qmt_ai_trading.datahub.qmt_provider import QmtHistoricalDataProvider, QmtProviderError


class FakeXtData:
    def __init__(self, use_ex: bool = True):
        self.connected = False
        self.download_calls = []
        self.market_calls = []
        self.use_ex = use_ex

    def connect(self):
        self.connected = True
        return True

    def download_history_data(self, symbol, period, start_time=None, end_time=None):
        self.download_calls.append((symbol, period, start_time, end_time))

    def get_market_data_ex(self, fields, symbols, period="1d", start_time="", end_time=""):
        if not self.use_ex:
            raise AttributeError("disabled")
        self.market_calls.append(("ex", tuple(symbols), period, start_time, end_time))
        return {symbols[0]: [{"time": "2024-01-01", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100, "amount": 150}]}


class FakeXtDataGet:
    def __init__(self):
        self.download_calls = []
        self.market_calls = []

    def download_history_data(self, symbol, period, start_time=None, end_time=None):
        self.download_calls.append((symbol, period, start_time, end_time))

    def get_market_data(self, fields, symbols, period="1d", start_time="", end_time=""):
        self.market_calls.append(("legacy", tuple(symbols), period, start_time, end_time))
        return {"time": ["2024-01-01"], "open": [1], "high": [2], "low": [0.5], "close": [1.5], "volume": [100], "amount": [150]}


class CountingProvider:
    name = "counting"

    def __init__(self):
        self.calls = 0

    def fetch_bars(self, query):
        self.calls += 1
        return FakeXtData().get_market_data_ex([], [query.symbols[0]])[query.symbols[0]]


def test_qmt_provider_error_is_exception():
    assert issubclass(QmtProviderError, Exception)


def test_fake_xtdata_provider_available_and_connects():
    fake = FakeXtData()
    provider = QmtHistoricalDataProvider(xtdata_module=fake)
    assert provider.is_available() is True
    assert provider.connect() is True
    assert fake.connected is True


def test_fetch_bars_calls_download_and_get_market_data_ex():
    fake = FakeXtData()
    provider = QmtHistoricalDataProvider(xtdata_module=fake)
    query = BarQuery(["510300.SH"], "2024-01-01", "2024-01-10", "1d", provider="qmt")
    bars = provider.fetch_bars(query)
    assert fake.download_calls == [("510300.SH", "1d", "20240101", "20240110")]
    assert fake.market_calls[0][0] == "ex"
    assert bars[0].symbol == "510300.SH"
    assert bars[0].datetime == "2024-01-01"
    assert bars[0].close == 1.5
    assert bars[0].amount == 150.0


def test_fetch_bars_uses_legacy_get_market_data_dict_lists():
    fake = FakeXtDataGet()
    provider = QmtHistoricalDataProvider(xtdata_module=fake)
    query = BarQuery(["510300.SH"], "2024-01-01", "2024-01-10", "1d", provider="qmt")
    bars = provider.fetch_bars(query)
    assert fake.market_calls[0][0] == "legacy"
    assert bars[0].open == 1.0


def test_factory_returns_mock_and_qmt():
    assert isinstance(create_historical_provider("mock"), MockHistoricalDataProvider)
    assert isinstance(create_historical_provider("qmt", xtdata_module=FakeXtData()), QmtHistoricalDataProvider)


def test_fetch_historical_bars_cache_hit_skips_provider(tmp_path: Path):
    store = LocalBarStore(tmp_path)
    query = BarQuery(["510300.SH"], "2024-01-01", "2024-01-01", "1d")
    store.save_bars("510300.SH", "1d", [{"symbol": "510300.SH", "datetime": "2024-01-01", "open": 1, "high": 1, "low": 1, "close": 1}], provider="seed")
    provider = CountingProvider()
    result = fetch_historical_bars(query, store=store, provider=provider)
    assert result.hit is True
    assert provider.calls == 0
    assert len(result.bars) == 1


def test_fetch_historical_bars_cache_miss_calls_provider_and_saves(tmp_path: Path):
    fake = FakeXtData()
    provider = QmtHistoricalDataProvider(xtdata_module=fake)
    store = LocalBarStore(tmp_path)
    query = BarQuery(["510300.SH"], "2024-01-01", "2024-01-01", "1d", provider="qmt")
    result = fetch_historical_bars(query, store=store, provider=provider)
    assert result.hit is False
    assert fake.download_calls
    assert len(result.bars) == 1
    assert Path(result.metadata[0].path).exists()


def test_market_data_cached_qmt_provider_with_fake(tmp_path: Path):
    bars = get_historical_bars_cached(["510300.SH"], "2024-01-01", "2024-01-01", provider="qmt", cache_root=str(tmp_path), xtdata_module=FakeXtData())
    assert len(bars) == 1
    assert bars[0].source == "qmt"


def test_scripts_import_main():
    from scripts.check_qmt_data_provider import main as check_main
    from scripts.fetch_history_cache import main as fetch_main

    assert callable(check_main)
    assert callable(fetch_main)
