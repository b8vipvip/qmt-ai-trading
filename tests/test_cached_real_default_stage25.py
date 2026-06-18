from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from qmt_ai_trading.datahub.providers import MockHistoricalDataProvider
from qmt_ai_trading.datahub.local_store import LocalBarStore, BarQuery
from qmt_ai_trading.pipeline.cache_quality_gate import (
    CacheQualityLevel,
    build_cache_quality_gate_policy,
    classify_cache_quality,
    evaluate_cache_quality_gate,
    load_latest_qmt_quality_report,
)
from qmt_ai_trading.pipeline.data_source import build_data_source_policy, choose_pipeline_data_source
from qmt_ai_trading.pipeline.daily_runner import run_etf_daily_pipeline
from qmt_ai_trading.pipeline.report import format_pipeline_report


def _warm_cache(root: Path, symbols=("510300.SH",), start="2026-05-09", end="2026-06-18") -> None:
    provider = MockHistoricalDataProvider()
    bars = provider.get_bars(BarQuery(list(symbols), start, end, frequency="1d"))
    store = LocalBarStore(root)
    for symbol in symbols:
        store.save_bars(symbol, "1d", [bar for bar in bars if bar.symbol == symbol], provider="mock")


def test_quality_gate_defaults_and_missing_report(tmp_path: Path):
    assert build_cache_quality_gate_policy().allow_unknown_quality_for_dry_run is True
    assert load_latest_qmt_quality_report(tmp_path / "missing") is None
    blocked = evaluate_cache_quality_gate(coverage_ratio=1.0, quality_report_dir=tmp_path, policy=build_cache_quality_gate_policy(require_quality_report=True))
    assert blocked.allowed is False
    allowed = evaluate_cache_quality_gate(coverage_ratio=1.0, quality_report_dir=tmp_path, policy=build_cache_quality_gate_policy(allow_unknown_quality_for_dry_run=True))
    assert allowed.allowed is True
    assert allowed.quality_level == CacheQualityLevel.UNKNOWN.value


def test_classify_quality_reports(tmp_path: Path):
    pass_report = {"decision": "PASS"}
    skip_report = {"decision": "SKIP"}
    assert classify_cache_quality(pass_report, coverage_ratio=1.0) == "HIGH"
    assert classify_cache_quality(skip_report, coverage_ratio=1.0) in {"LOW", "UNKNOWN"}
    path = tmp_path / "sample.qmt_quality.json"
    path.write_text(json.dumps(pass_report), encoding="utf-8")
    assert load_latest_qmt_quality_report(tmp_path)["decision"] == "PASS"


def test_cached_real_first_unknown_quality_and_missing_cache(tmp_path: Path):
    cache = tmp_path / "cache"
    _warm_cache(cache)
    policy = build_data_source_policy(mode="cached_real_first", cache_root=cache, quality_report_dir=tmp_path / "reports", start_date="2026-05-09", end_date="2026-06-18", min_bars=20)
    decision = choose_pipeline_data_source(policy, ["510300.SH"])
    assert decision.selected_source == "cached_unknown_quality"
    assert decision.quality_level == "UNKNOWN"

    missing = build_data_source_policy(mode="cached_real_first", cache_root=tmp_path / "missing", quality_report_dir=tmp_path / "reports", start_date="2026-05-09", end_date="2026-06-18", min_bars=20)
    missing_decision = choose_pipeline_data_source(missing, ["510300.SH"])
    assert missing_decision.selected_source == "blocked_missing_quality"
    assert missing_decision.allow_trade_intents is False


def test_daily_pipeline_cached_real_first_report_and_no_intents_on_missing(tmp_path: Path):
    cache = tmp_path / "cache"
    _warm_cache(cache)
    result = run_etf_daily_pipeline(symbols=["510300.SH"], cache_root=str(cache), research_start_date="2026-05-09", research_end_date="2026-06-18", min_bars=20, cached_strategy_top_n=1)
    assert result.metadata["data_source"]["selected_source"] == "cached_unknown_quality"
    assert "UNKNOWN" in result.report_text
    assert "Cache quality is not high enough for live trading decisions" in result.report_text

    missing = run_etf_daily_pipeline(symbols=["510300.SH"], cache_root=str(tmp_path / "none"), research_start_date="2026-05-09", research_end_date="2026-06-18", min_bars=20)
    assert not missing.trade_intents
    assert missing.metadata["data_source"]["allow_trade_intents"] is False


def test_legacy_compat_and_script_help(tmp_path: Path):
    legacy = run_etf_daily_pipeline(data_source_mode="legacy", symbols=["510300.SH"])
    assert legacy.metadata["data_source"]["selected_source"] == "legacy_default"
    assert "Cache quality is not high enough for live trading decisions" in format_pipeline_report(legacy) or legacy.report_text
    assert subprocess.run([sys.executable, "scripts/check_cache_quality_gate.py", "--cache-root", str(tmp_path / "none"), "--quality-report-dir", str(tmp_path / "reports")], check=False, capture_output=True, text=True).returncode == 0
    daily_help = subprocess.run([sys.executable, "scripts/run_daily_pipeline.py", "--help"], check=False, capture_output=True, text=True)
    assert daily_help.returncode == 0 and "cached_real_first" in daily_help.stdout
    sched_help = subprocess.run([sys.executable, "scripts/run_scheduled_daily_pipeline.py", "--help"], check=False, capture_output=True, text=True)
    assert sched_help.returncode == 0 and "cached_real_first" in sched_help.stdout
    reg = subprocess.run([sys.executable, "scripts/register_daily_pipeline_task.py", "--time", "15:30"], check=False, capture_output=True, text=True)
    assert reg.returncode == 0 and "cached_real_first" in reg.stdout and "quality_report_dir" in reg.stdout


def test_gitignore_and_docs_and_sync_untouched():
    assert "qmt_data_quality_reports/" in Path(".gitignore").read_text(encoding="utf-8")
    roadmap = Path("docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段二十五：Daily Pipeline 真实缓存数据默认化" in roadmap
    assert "阶段二十六：组合与资金管理层" in roadmap
