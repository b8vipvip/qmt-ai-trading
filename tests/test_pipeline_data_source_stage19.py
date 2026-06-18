from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from qmt_ai_trading.datahub.local_store import LocalBarStore
from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.pipeline.daily_runner import run_etf_daily_pipeline
from qmt_ai_trading.pipeline.data_source import (
    PipelineDataSourcePolicy,
    build_data_source_policy,
    choose_pipeline_data_source,
    evaluate_cache_coverage,
    load_pipeline_research_data,
)
from qmt_ai_trading.pipeline.report import format_pipeline_report


def _bars(symbol: str, count: int = 25) -> list[MarketBar]:
    start = datetime(2024, 1, 1)
    return [MarketBar(symbol, (start + timedelta(days=i)).date().isoformat(), 10 + i, 11 + i, 9 + i, 10.5 + i, 1000 + i) for i in range(count)]


def test_policy_instantiates_and_default_mode_legacy() -> None:
    assert PipelineDataSourcePolicy().mode == "legacy"
    assert build_data_source_policy().mode == "legacy"


def test_evaluate_cache_coverage_complete_and_missing(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    policy = build_data_source_policy(mode="cached", cache_root=tmp_path, start_date="2024-01-01", end_date="2024-01-25", min_bars=20)
    decision, _ = evaluate_cache_coverage(policy, ["510300.SH"])
    assert decision.coverage_ratio == 1
    missing, _ = evaluate_cache_coverage(policy, ["510500.SH"])
    assert missing.coverage_ratio == 0


def test_choose_cached_complete_and_insufficient(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    policy = build_data_source_policy(mode="cached", cache_root=tmp_path, start_date="2024-01-01", end_date="2024-01-25", min_bars=20)
    assert choose_pipeline_data_source(policy, ["510300.SH"]).selected_source == "cached_research"
    decision = choose_pipeline_data_source(policy, ["510500.SH"])
    assert decision.allow_trade_intents is False


def test_auto_fallback_low_confidence(tmp_path: Path) -> None:
    policy = build_data_source_policy(mode="auto", allow_mock_fallback=True, cache_root=tmp_path, start_date="2024-01-01", end_date="2024-01-25", min_bars=20)
    decision = choose_pipeline_data_source(policy, ["510300.SH"])
    assert decision.selected_source == "mock_fallback"
    assert decision.fallback_used is True
    assert decision.confidence == "LOW"


def test_load_pipeline_research_data_returns_candidates(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    policy = build_data_source_policy(mode="cached", cache_root=tmp_path, start_date="2024-01-01", end_date="2024-01-25", min_bars=20)
    result = load_pipeline_research_data(policy, ["510300.SH"], top_n=1, capital=100000)
    assert result.decision.selected_source == "cached_research"
    assert result.candidates


def test_daily_pipeline_cached_enough_missing_and_auto_fallback(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    ok = run_etf_daily_pipeline(symbols=["510300.SH"], data_source_mode="cached", cache_root=str(tmp_path), research_start_date="2024-01-01", research_end_date="2024-01-25", min_bars=20, cached_strategy_top_n=1)
    assert ok.trade_intents
    empty = run_etf_daily_pipeline(symbols=["510500.SH"], data_source_mode="cached", cache_root=str(tmp_path), research_start_date="2024-01-01", research_end_date="2024-01-25", min_bars=20)
    assert not empty.trade_intents
    fallback = run_etf_daily_pipeline(symbols=["510500.SH"], data_source_mode="auto", allow_mock_fallback=True, cache_root=str(tmp_path), research_start_date="2024-01-01", research_end_date="2024-01-25", min_bars=20)
    assert fallback.metadata["data_source"]["selected_source"] == "mock_fallback"
    assert "mock/fallback data" in fallback.report_text


def test_format_pipeline_report_has_data_source(tmp_path: Path) -> None:
    result = run_etf_daily_pipeline(symbols=["510500.SH"], data_source_mode="auto", allow_mock_fallback=True, cache_root=str(tmp_path), research_start_date="2024-01-01", research_end_date="2024-01-25")
    report = format_pipeline_report(result)
    assert "## Data Source" in report


def test_stage19_scripts_run(tmp_path: Path) -> None:
    LocalBarStore(tmp_path).save_bars("510300.SH", "1d", _bars("510300.SH", 25))
    cmds = [
        [sys.executable, "scripts/check_pipeline_data_source.py", "--data-source-mode", "cached", "--symbols", "510300.SH", "--cache-root", str(tmp_path), "--start", "2024-01-01", "--end", "2024-01-25", "--min-bars", "20"],
        [sys.executable, "scripts/run_daily_pipeline.py", "--data-source-mode", "cached", "--symbols", "510300.SH", "--cache-root", str(tmp_path), "--research-start", "2024-01-01", "--research-end", "2024-01-25", "--min-bars", "20", "--cached-strategy-top-n", "1"],
        [sys.executable, "scripts/run_scheduled_daily_pipeline.py", "--warmup-universe", "--warmup-provider", "mock", "--universe-lookback-days", "25", "--warmup-end", "2024-01-25", "--cache-root", str(tmp_path / "scheduled"), "--data-source-mode", "cached", "--research-start", "2024-01-01", "--research-end", "2024-01-25", "--min-bars", "20", "--cached-strategy-top-n", "1"],
    ]
    for cmd in cmds:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        assert completed.returncode == 0, completed.stderr + completed.stdout
    registered = subprocess.run([sys.executable, "scripts/register_daily_pipeline_task.py", "--data-source-mode", "cached", "--time", "15:30"], capture_output=True, text=True, check=False)
    assert registered.returncode == 0
    assert "--data-source-mode cached" in registered.stdout
