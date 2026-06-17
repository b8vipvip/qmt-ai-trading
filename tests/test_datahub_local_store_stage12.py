from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

from qmt_ai_trading.datahub.local_store import BarQuery, LocalBarStore
from qmt_ai_trading.datahub.market_data import get_historical_bars_cached
from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.providers import MockHistoricalDataProvider, fetch_historical_bars


def _bars():
    return [
        MarketBar("510300.SH", "2024-01-01", 1, 2, 0.5, 1.5, 100, 150, "test"),
        MarketBar("510300.SH", "2024-01-02", 2, 3, 1.5, 2.5, 101, 250, "test"),
    ]


def test_bar_query_instantiates():
    query = BarQuery(symbols=["510300.SH"], start_date="2024-01-01", end_date="2024-01-02")
    assert query.frequency == "1d"


def test_local_store_save_load_and_coverage(tmp_path):
    store = LocalBarStore(tmp_path)
    metadata = store.save_bars("510300.SH", "1d", _bars(), provider="test")
    assert Path(metadata.path).exists()
    query = BarQuery(["510300.SH"], "2024-01-01", "2024-01-02", "1d")
    assert len(store.load_bars(query)) == 2
    assert store.has_coverage(query) is True
    assert store.has_coverage(BarQuery(["510300.SH"], "2023-12-31", "2024-01-02", "1d")) is False


def test_query_bars_hit(tmp_path):
    store = LocalBarStore(tmp_path)
    store.save_bars("510300.SH", "1d", _bars(), provider="test")
    result = store.query_bars(BarQuery(["510300.SH"], "2024-01-01", "2024-01-02", "1d"))
    assert result.hit is True
    assert len(result.bars) == 2


def test_mock_provider_is_stable():
    query = BarQuery(["510300.SH"], "2024-01-01", "2024-01-03", "1d")
    provider = MockHistoricalDataProvider()
    assert provider.get_bars(query) == provider.get_bars(query)


def test_fetch_historical_bars_miss_then_hit(tmp_path):
    query = BarQuery(["510300.SH"], "2024-01-01", "2024-01-03", "1d")
    store = LocalBarStore(tmp_path)
    first = fetch_historical_bars(query, store=store, provider=MockHistoricalDataProvider())
    second = fetch_historical_bars(query, store=store, provider=MockHistoricalDataProvider())
    assert first.hit is False
    assert second.hit is True
    assert len(first.bars) == len(second.bars) == 3


def test_get_historical_bars_cached(tmp_path):
    bars = get_historical_bars_cached("510300.SH", "2024-01-01", "2024-01-02", cache_root=str(tmp_path))
    assert len(bars) == 2


def test_fetch_history_cache_script_runs(tmp_path):
    script = Path("scripts/fetch_history_cache.py")
    completed = subprocess.run(
        [sys.executable, str(script), "--symbols", "510300.SH,510500.SH", "--start", "2024-01-01", "--end", "2024-01-03", "--frequency", "1d", "--cache-root", str(tmp_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    assert "cache miss" in completed.stdout
    completed2 = subprocess.run(
        [sys.executable, str(script), "--symbols", "510300.SH,510500.SH", "--start", "2024-01-01", "--end", "2024-01-03", "--frequency", "1d", "--cache-root", str(tmp_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    assert "cache hit" in completed2.stdout


def test_gitignore_contains_market_data():
    text = Path(".gitignore").read_text(encoding="utf-8")
    assert "market_data/" in text
    assert "data_cache/" in text


def test_sync_all_not_modified_guard():
    data = Path("scripts/sync_all.ps1").read_bytes()
    assert hashlib.sha256(data).hexdigest()
