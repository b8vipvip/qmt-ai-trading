from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qmt_ai_trading.datahub.cache_warmup import (
    CacheWarmupRequest,
    build_default_warmup_request,
    format_cache_warmup_result,
    warmup_history_cache,
)
from qmt_ai_trading.scheduler.models import ScheduleConfig
from qmt_ai_trading.scheduler.windows_task import build_daily_pipeline_command


def test_cache_warmup_request_instantiates(tmp_path: Path) -> None:
    req = CacheWarmupRequest(["510300.SH"], "2024-01-01", "2024-01-10", cache_root=tmp_path)
    assert req.provider == "mock"
    assert req.fail_fast is False


def test_build_default_warmup_request(tmp_path: Path) -> None:
    req = build_default_warmup_request(symbols=["510300.sh"], start_date="2024-01-01", end_date="2024-01-02", cache_root=tmp_path)
    assert req.symbols == ["510300.SH"]
    assert req.frequency == "1d"


def test_warmup_mock_first_miss_then_hit(tmp_path: Path) -> None:
    req = build_default_warmup_request(symbols=["510300.SH"], start_date="2024-01-01", end_date="2024-01-03", provider="mock", cache_root=tmp_path)
    first = warmup_history_cache(req)
    assert first.success is True
    assert first.miss_count == 1
    assert first.fetched_count == 1
    second = warmup_history_cache(req)
    assert second.success is True
    assert second.hit_count == 1
    assert second.fetched_count == 0


def test_warmup_fail_fast_false_continues(monkeypatch, tmp_path: Path) -> None:
    import qmt_ai_trading.datahub.cache_warmup as module

    real_fetch = module.fetch_historical_bars

    def flaky(query, *args, **kwargs):
        if query.symbols == ["510500.SH"]:
            raise RuntimeError("fake provider failure")
        return real_fetch(query, *args, **kwargs)

    monkeypatch.setattr(module, "fetch_historical_bars", flaky)
    req = build_default_warmup_request(symbols=["510300.SH", "510500.SH", "159915.SZ"], start_date="2024-01-01", end_date="2024-01-02", cache_root=tmp_path, fail_fast=False)
    result = warmup_history_cache(req)
    assert result.failed_count == 1
    assert len(result.items) == 3
    assert result.fetched_count == 2


def test_warmup_fail_fast_true_aborts(monkeypatch, tmp_path: Path) -> None:
    import qmt_ai_trading.datahub.cache_warmup as module

    def always_fail(query, *args, **kwargs):
        raise RuntimeError("fake provider failure")

    monkeypatch.setattr(module, "fetch_historical_bars", always_fail)
    req = build_default_warmup_request(symbols=["510300.SH", "510500.SH"], start_date="2024-01-01", end_date="2024-01-02", cache_root=tmp_path, fail_fast=True)
    result = warmup_history_cache(req)
    assert result.failed_count == 1
    assert len(result.items) == 1
    assert result.metadata["aborted"] is True


def test_format_cache_warmup_result_returns_string(tmp_path: Path) -> None:
    req = build_default_warmup_request(symbols=["510300.SH"], start_date="2024-01-01", end_date="2024-01-01", cache_root=tmp_path)
    text = format_cache_warmup_result(warmup_history_cache(req))
    assert "Cache warmup summary" in text


def test_warmup_script_mock_runs(tmp_path: Path) -> None:
    completed = subprocess.run([sys.executable, "scripts/warmup_history_cache.py", "--symbols", "510300.SH,510500.SH", "--start", "2024-01-01", "--end", "2024-01-02", "--frequency", "1d", "--provider", "mock", "--cache-root", str(tmp_path)], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "Cache warmup summary" in completed.stdout


def test_run_scheduled_pipeline_warmup_mock_runs(tmp_path: Path) -> None:
    completed = subprocess.run([sys.executable, "scripts/run_scheduled_daily_pipeline.py", "--warmup-cache", "--warmup-provider", "mock", "--warmup-start", "2024-01-01", "--warmup-end", "2024-01-02", "--warmup-frequency", "1d", "--cache-root", str(tmp_path)], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "Scheduled dry-run pipeline finished" in completed.stdout


def test_register_script_warmup_dry_run_command_contains_args() -> None:
    completed = subprocess.run([sys.executable, "scripts/register_daily_pipeline_task.py", "--warmup-cache", "--warmup-provider", "mock", "--warmup-start", "2024-01-01", "--warmup-end", "2024-01-10", "--warmup-frequency", "1d", "--cache-root", "market_data", "--time", "15:30"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "--warmup-cache" in completed.stdout
    assert "--warmup-provider mock" in completed.stdout


def test_build_daily_pipeline_command_supports_warmup() -> None:
    command = build_daily_pipeline_command(script_path="scripts/run_scheduled_daily_pipeline.py", warmup_cache=True, warmup_provider="mock", warmup_start="2024-01-01", warmup_end="2024-01-10", cache_root="market_data")
    assert "--warmup-cache" in command.arguments
    assert "--cache-root" in command.arguments


def test_schedule_config_has_warmup_fields() -> None:
    cfg = ScheduleConfig(warmup_cache=True, warmup_start="2024-01-01", warmup_end="2024-01-02")
    assert cfg.warmup_cache is True


def test_qmt_provider_without_xtquant_does_not_crash(tmp_path: Path) -> None:
    req = build_default_warmup_request(symbols=["510300.SH"], start_date="2024-01-01", end_date="2024-01-02", provider="qmt", cache_root=tmp_path)
    result = warmup_history_cache(req)
    assert result.total_symbols == 1
    assert result.failed_count + result.skipped_count in (0, 1)


def test_gitignore_contains_stage15() -> None:
    assert "market_data_test_stage15/" in Path(".gitignore").read_text(encoding="utf-8")


def test_sync_all_ps1_not_modified_stage15() -> None:
    completed = subprocess.run(["git", "diff", "--", "scripts/sync_all.ps1"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert completed.stdout == ""
