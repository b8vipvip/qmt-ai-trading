from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qmt_ai_trading.datahub.local_store import LocalBarStore
from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.pipeline.daily_runner import run_etf_daily_pipeline
from qmt_ai_trading.research.cache_reader import CachedResearchRequest, load_cached_bars_for_symbol, load_cached_research_dataset
from qmt_ai_trading.research.cache_scoring import build_candidates_from_cached_research, score_etf_universe_from_cache, score_symbols_from_cache
from qmt_ai_trading.research.scoring import ResearchScore
from qmt_ai_trading.strategies.etf_rotation import ETFCandidate


def _bars(symbol: str, n: int = 25) -> list[MarketBar]:
    return [MarketBar(symbol, f"2024-01-{i+1:02d}", 1+i/100, 1.1+i/100, 0.9+i/100, 1.0+i/100, 1000+i) for i in range(n)]


def test_cached_research_request_instantiates(tmp_path: Path) -> None:
    req = CachedResearchRequest(["510300.SH"], "2024-01-01", "2024-01-10", cache_root=tmp_path)
    assert req.frequency == "1d"


def test_load_cached_bars_for_symbol_reads_store(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 10))
    item = load_cached_bars_for_symbol("510300.SH", "2024-01-01", "2024-01-10", cache_root=tmp_path, min_bars=5)
    assert item.success is True
    assert item.bar_count == 10


def test_load_cached_bars_for_symbol_missing_does_not_crash(tmp_path: Path) -> None:
    item = load_cached_bars_for_symbol("510300.SH", "2024-01-01", "2024-01-10", cache_root=tmp_path, min_bars=1)
    assert item.success is False
    assert "cache miss" in item.message


def test_load_cached_research_dataset_partial_success(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 10))
    dataset = load_cached_research_dataset(CachedResearchRequest(["510300.SH", "510500.SH"], "2024-01-01", "2024-01-10", cache_root=tmp_path, min_bars=5))
    assert dataset.success is True
    assert dataset.loaded_symbols == 1
    assert dataset.failed_symbols == 1


def test_min_bars_filters_insufficient_symbol(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 3))
    item = load_cached_bars_for_symbol("510300.SH", "2024-01-01", "2024-01-03", cache_root=tmp_path, min_bars=5)
    assert item.success is False
    assert "insufficient" in item.message


def test_score_symbols_from_cache_returns_research_score(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    scores, dataset = score_symbols_from_cache(["510300.SH"], "2024-01-01", "2024-01-25", cache_root=tmp_path, min_bars=20)
    assert dataset.success is True
    assert isinstance(scores[0], ResearchScore)
    assert scores[0].metrics["source"] == "cached_research"


def test_score_etf_universe_from_cache_default(tmp_path: Path) -> None:
    for symbol in ["510300.SH", "510500.SH", "159915.SZ", "512100.SH", "588000.SH"]:
        LocalBarStore(tmp_path).save_bars(symbol, "1d", _bars(symbol, 25))
    scores, dataset = score_etf_universe_from_cache(start_date="2024-01-01", end_date="2024-01-25", cache_root=tmp_path, min_bars=20)
    assert len(scores) >= 5
    assert dataset.loaded_symbols >= 5


def test_build_candidates_from_cached_research_returns_etf_candidate(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    scores, dataset = score_symbols_from_cache(["510300.SH"], "2024-01-01", "2024-01-25", cache_root=tmp_path, min_bars=20)
    candidates = build_candidates_from_cached_research(scores, dataset=dataset)
    assert isinstance(candidates[0], ETFCandidate)
    assert candidates[0].metrics["source"] == "cached_research"


def test_run_etf_daily_pipeline_cached_research_runs(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    result = run_etf_daily_pipeline(symbols=["510300.SH"], use_cached_research=True, cache_root=str(tmp_path), research_start_date="2024-01-01", research_end_date="2024-01-25", min_bars=20)
    assert result.success is True
    assert any(step.name == "cached_research" for step in result.steps)


def test_pipeline_cached_research_missing_warns_not_crash(tmp_path: Path) -> None:
    result = run_etf_daily_pipeline(symbols=["510300.SH"], use_cached_research=True, cache_root=str(tmp_path), research_start_date="2024-01-01", research_end_date="2024-01-25", min_bars=20)
    assert result.success is True
    assert "warning" in [step.message for step in result.steps if step.name == "cached_research"][0]


def test_run_cached_research_script_runs(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    completed = subprocess.run([sys.executable, "scripts/run_cached_research.py", "--symbols", "510300.SH", "--start", "2024-01-01", "--end", "2024-01-25", "--cache-root", str(tmp_path), "--min-bars", "20"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "Cached Research Dataset" in completed.stdout


def test_run_daily_pipeline_cached_research_script_runs(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    completed = subprocess.run([sys.executable, "scripts/run_daily_pipeline.py", "--symbols", "510300.SH", "--use-cached-research", "--cache-root", str(tmp_path), "--research-start", "2024-01-01", "--research-end", "2024-01-25", "--min-bars", "20"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "cached_research" in completed.stdout


def test_scheduled_pipeline_warmup_and_cached_research_runs(tmp_path: Path) -> None:
    completed = subprocess.run([sys.executable, "scripts/run_scheduled_daily_pipeline.py", "--warmup-universe", "--warmup-provider", "mock", "--universe-lookback-days", "5", "--warmup-end", "2024-01-25", "--cache-root", str(tmp_path), "--use-cached-research", "--research-start", "2024-01-20", "--research-end", "2024-01-25", "--min-bars", "5"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "Scheduled dry-run pipeline finished" in completed.stdout


def test_register_daily_pipeline_task_cached_research_contains_args() -> None:
    completed = subprocess.run([sys.executable, "scripts/register_daily_pipeline_task.py", "--warmup-universe", "--warmup-provider", "mock", "--universe-lookback-days", "10", "--cache-root", "market_data", "--use-cached-research", "--research-start", "2026-06-08", "--research-end", "2026-06-18", "--research-frequency", "1d", "--min-bars", "5", "--time", "15:30"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "--use-cached-research" in completed.stdout
    assert "--min-bars 5" in completed.stdout


def test_sync_all_ps1_not_modified_stage17() -> None:
    completed = subprocess.run(["git", "diff", "--", "scripts/sync_all.ps1"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert completed.stdout == ""
