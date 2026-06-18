from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qmt_ai_trading.datahub.local_store import LocalBarStore
from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.pipeline.daily_runner import run_etf_daily_pipeline
from qmt_ai_trading.research.cache_scoring import score_symbols_from_cache
from qmt_ai_trading.strategies.cached_etf_rotation import (
    CachedETFSignalConfig,
    build_cached_etf_candidates,
    generate_cached_etf_rotation_intents,
    select_cached_etf_candidates,
)


def _bars(symbol: str, n: int = 25) -> list[MarketBar]:
    return [MarketBar(symbol, f"2024-01-{i+1:02d}", 1+i/100, 1.1+i/100, 0.9+i/100, 1.0+i/80, 1000+i*10) for i in range(n)]


def test_config_instantiates() -> None:
    assert CachedETFSignalConfig(top_n=1).min_bars == 20


def test_build_candidates_enough_and_insufficient(tmp_path: Path) -> None:
    store = LocalBarStore(tmp_path)
    store.save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    store.save_bars("510500.SH", "1d", _bars("510500.SH", 5))
    scores, _ = score_symbols_from_cache(["510300.SH", "510500.SH"], "2024-01-01", "2024-01-25", cache_root=tmp_path, min_bars=20)
    candidates, skipped = build_cached_etf_candidates(scores, CachedETFSignalConfig(min_bars=20))
    assert any(c.symbol == "510300.SH" and c.eligible for c in candidates)
    assert any(item["symbol"] == "510500.SH" and "insufficient" in item["reason"] for item in skipped)


def test_select_top_n_and_intents_are_safe_lots() -> None:
    candidates, _ = build_cached_etf_candidates([
        type("S", (), {"symbol": "510300.SH", "score": 60.0, "eligible": True, "reason": "", "metrics": {"bar_count": 25, "source": "cached_research"}})(),
        type("S", (), {"symbol": "510500.SH", "score": 80.0, "eligible": True, "reason": "", "metrics": {"bar_count": 25, "source": "cached_research"}})(),
    ], CachedETFSignalConfig(top_n=1, max_position_pct=0.1))
    selected = select_cached_etf_candidates(candidates, CachedETFSignalConfig(top_n=1))
    assert selected[0].symbol == "510500.SH"
    intents = generate_cached_etf_rotation_intents(candidates, CachedETFSignalConfig(top_n=1, max_position_pct=0.1), capital=100000)
    assert intents and intents[0].dry_run is True
    assert intents[0].quantity % 100 == 0
    assert intents[0].target_percent <= 0.1


def test_score_symbols_from_cache_enough_returns_numeric(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    scores, _ = score_symbols_from_cache(["510300.SH"], "2024-01-01", "2024-01-25", cache_root=tmp_path, min_bars=20)
    assert scores[0].score is not None
    assert scores[0].eligible is True
    assert "cached factor score" in scores[0].reason


def test_daily_pipeline_cached_enough_and_insufficient(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    ok = run_etf_daily_pipeline(symbols=["510300.SH"], use_cached_research=True, cache_root=str(tmp_path), research_start_date="2024-01-01", research_end_date="2024-01-25", min_bars=20, cached_strategy_top_n=1, cached_strategy_min_bars=20)
    assert ok.success is True
    assert len(ok.trade_intents) >= 1
    assert any(step.name == "cached_etf_rotation" for step in ok.steps)
    empty = run_etf_daily_pipeline(symbols=["510500.SH"], use_cached_research=True, cache_root=str(tmp_path), research_start_date="2024-01-01", research_end_date="2024-01-25", min_bars=20, cached_strategy_top_n=1, cached_strategy_min_bars=20)
    assert empty.success is True
    assert len(empty.trade_intents) == 0


def test_scripts_and_scheduler_args_run(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    commands = [
        [sys.executable, "scripts/run_cached_etf_signal.py", "--symbols", "510300.SH", "--start", "2024-01-01", "--end", "2024-01-25", "--cache-root", str(tmp_path), "--min-bars", "20", "--top-n", "1"],
        [sys.executable, "scripts/run_daily_pipeline.py", "--symbols", "510300.SH", "--use-cached-research", "--cache-root", str(tmp_path), "--research-start", "2024-01-01", "--research-end", "2024-01-25", "--min-bars", "20", "--cached-strategy-top-n", "1"],
        [sys.executable, "scripts/run_scheduled_daily_pipeline.py", "--warmup-universe", "--warmup-provider", "mock", "--universe-lookback-days", "25", "--warmup-end", "2024-01-25", "--cache-root", str(tmp_path / "scheduled"), "--use-cached-research", "--research-start", "2024-01-01", "--research-end", "2024-01-25", "--min-bars", "20", "--cached-strategy-top-n", "1"],
    ]
    for command in commands:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        assert completed.returncode == 0, completed.stderr + completed.stdout
    registered = subprocess.run([sys.executable, "scripts/register_daily_pipeline_task.py", "--use-cached-research", "--cached-strategy-top-n", "1", "--time", "15:30"], capture_output=True, text=True, check=False)
    assert registered.returncode == 0
    assert "--cached-strategy-top-n 1" in registered.stdout


def test_sync_all_ps1_not_modified_stage18() -> None:
    completed = subprocess.run(["git", "diff", "--", "scripts/sync_all.ps1"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert completed.stdout == ""
