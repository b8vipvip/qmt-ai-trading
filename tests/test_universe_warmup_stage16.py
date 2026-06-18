from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qmt_ai_trading.datahub.universe_warmup import (
    build_universe_warmup_request,
    format_universe_warmup_result,
    resolve_universe_symbols,
    resolve_warmup_date_range,
    warmup_etf_universe_history,
)
from qmt_ai_trading.scheduler.windows_task import build_daily_pipeline_command


def test_resolve_universe_symbols_default_returns_etfs() -> None:
    symbols = resolve_universe_symbols()
    assert "510300.SH" in symbols
    assert symbols


def test_resolve_universe_symbols_explicit_wins() -> None:
    assert resolve_universe_symbols(symbols="510300.sh,159915.sz") == ["510300.SH", "159915.SZ"]


def test_resolve_date_range_start_end() -> None:
    assert resolve_warmup_date_range("2024-01-01", "2024-01-10") == ("2024-01-01", "2024-01-10")


def test_resolve_date_range_lookback_days() -> None:
    assert resolve_warmup_date_range(end_date="2024-01-10", lookback_days=9) == ("2024-01-01", "2024-01-10")


def test_resolve_date_range_lookback_years() -> None:
    assert resolve_warmup_date_range(end_date="2025-01-01", lookback_years=1) == ("2024-01-02", "2025-01-01")


def test_build_universe_warmup_request_instantiates(tmp_path: Path) -> None:
    req = build_universe_warmup_request(symbols=["510300.SH"], start_date="2024-01-01", end_date="2024-01-02", cache_root=tmp_path)
    assert req.symbols == ["510300.SH"]
    assert req.provider == "mock"


def test_warmup_universe_mock_first_fetched_then_hit(tmp_path: Path) -> None:
    req = build_universe_warmup_request(symbols=["510300.SH"], start_date="2024-01-01", end_date="2024-01-03", cache_root=tmp_path)
    first = warmup_etf_universe_history(req)
    assert first.success is True
    assert first.warmup_result.fetched_count == 1
    second = warmup_etf_universe_history(req)
    assert second.success is True
    assert second.warmup_result.hit_count == 1


def test_format_universe_warmup_result_returns_string(tmp_path: Path) -> None:
    req = build_universe_warmup_request(symbols=["510300.SH"], start_date="2024-01-01", end_date="2024-01-01", cache_root=tmp_path)
    assert "Universe warmup summary" in format_universe_warmup_result(warmup_etf_universe_history(req))


def test_warmup_etf_universe_script_mock_runs(tmp_path: Path) -> None:
    completed = subprocess.run([sys.executable, "scripts/warmup_etf_universe.py", "--symbols", "510300.SH", "--lookback-days", "2", "--end", "2024-01-03", "--provider", "mock", "--cache-root", str(tmp_path)], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "Universe warmup summary" in completed.stdout


def test_run_scheduled_daily_pipeline_warmup_universe_runs(tmp_path: Path) -> None:
    completed = subprocess.run([sys.executable, "scripts/run_scheduled_daily_pipeline.py", "--warmup-universe", "--warmup-provider", "mock", "--universe-lookback-days", "2", "--warmup-end", "2024-01-03", "--warmup-frequency", "1d", "--cache-root", str(tmp_path)], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "Scheduled dry-run pipeline finished" in completed.stdout


def test_register_daily_pipeline_task_warmup_universe_contains_args() -> None:
    completed = subprocess.run([sys.executable, "scripts/register_daily_pipeline_task.py", "--warmup-universe", "--warmup-provider", "mock", "--universe-lookback-days", "10", "--warmup-frequency", "1d", "--cache-root", "market_data", "--time", "15:30"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "--warmup-universe" in completed.stdout
    assert "--universe-lookback-days 10" in completed.stdout


def test_build_daily_pipeline_command_supports_warmup_universe() -> None:
    command = build_daily_pipeline_command(script_path="scripts/run_scheduled_daily_pipeline.py", warmup_universe=True, universe_name="default_etf", universe_lookback_days=10, warmup_provider="mock")
    assert "--warmup-universe" in command.arguments
    assert "--universe-lookback-days" in command.arguments


def test_project_roadmap_exists_and_contains_rules() -> None:
    text = Path("docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "后续 Codex 开发规则" in text
    assert "AI 不直接下单" in text
    assert "QMT Gateway 是唯一真实交易边界" in text


def test_gitignore_contains_stage16() -> None:
    assert "market_data_test_stage16/" in Path(".gitignore").read_text(encoding="utf-8")


def test_sync_all_ps1_not_modified_stage16() -> None:
    completed = subprocess.run(["git", "diff", "--", "scripts/sync_all.ps1"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert completed.stdout == ""
