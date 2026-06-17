from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qmt_ai_trading.scheduler.models import ScheduleConfig
from qmt_ai_trading.scheduler.windows_task import (
    build_daily_pipeline_command,
    build_schtasks_create_command,
    build_schtasks_delete_command,
    query_windows_task,
    register_windows_task,
    unregister_windows_task,
)


def test_schedule_config_instantiates() -> None:
    config = ScheduleConfig()
    assert config.task_name == "QmtAiTradingDailyDryRun"
    assert config.run_time == "15:30"
    assert config.dry_run is True


def test_build_daily_pipeline_command_defaults() -> None:
    command = build_daily_pipeline_command()
    display = command.metadata["display"]
    assert command.command == "py"
    assert "scripts/run_daily_pipeline.py" in display
    assert "--write-reports" in command.arguments
    assert "--report-dir" in command.arguments
    assert "reports" in command.arguments
    assert "--notify-dry-run" in command.arguments


def test_build_schtasks_create_command_contains_create() -> None:
    command = build_schtasks_create_command(ScheduleConfig(project_root=Path.cwd()))
    display = command.metadata["display"]
    assert command.command == "schtasks"
    assert "/Create" in command.arguments
    assert "schtasks" in display
    assert "QmtAiTradingDailyDryRun" in display


def test_build_schtasks_delete_command_contains_delete() -> None:
    command = build_schtasks_delete_command()
    assert command.command == "schtasks"
    assert "/Delete" in command.arguments


def test_register_windows_task_dry_run_does_not_call_subprocess(monkeypatch) -> None:
    def fail_run(*args, **kwargs):  # pragma: no cover - should not be called
        raise AssertionError("subprocess.run should not be called in dry-run")

    monkeypatch.setattr("qmt_ai_trading.scheduler.windows_task.subprocess.run", fail_run)
    result = register_windows_task(ScheduleConfig(project_root=Path.cwd()), dry_run=True)
    assert result.success is True
    assert result.dry_run is True
    assert result.metadata["executed"] is False


def test_unregister_windows_task_dry_run_does_not_call_subprocess(monkeypatch) -> None:
    monkeypatch.setattr("qmt_ai_trading.scheduler.windows_task.subprocess.run", lambda *a, **k: (_ for _ in ()).throw(AssertionError()))
    result = unregister_windows_task(dry_run=True)
    assert result.success is True
    assert result.dry_run is True


def test_query_windows_task_dry_run_does_not_call_subprocess(monkeypatch) -> None:
    monkeypatch.setattr("qmt_ai_trading.scheduler.windows_task.subprocess.run", lambda *a, **k: (_ for _ in ()).throw(AssertionError()))
    result = query_windows_task(dry_run=True)
    assert result.success is True
    assert result.dry_run is True


def test_register_script_default_dry_run_runs() -> None:
    completed = subprocess.run([sys.executable, "scripts/register_daily_pipeline_task.py"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "DRY-RUN ONLY" in completed.stdout
    assert "no task registered" in completed.stdout


def test_unregister_script_default_dry_run_runs() -> None:
    completed = subprocess.run([sys.executable, "scripts/unregister_daily_pipeline_task.py"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert "DRY-RUN ONLY" in completed.stdout
    assert "no task deleted" in completed.stdout


def test_run_scheduled_daily_pipeline_imports_main() -> None:
    from scripts.run_scheduled_daily_pipeline import main

    assert callable(main)


def test_gitignore_contains_runtime_outputs() -> None:
    text = Path(".gitignore").read_text(encoding="utf-8")
    assert "reports/" in text
    assert "logs/" in text
    assert "reports_test_stage10/" in text
    assert "*.log" in text


def test_sync_all_ps1_not_modified() -> None:
    completed = subprocess.run(["git", "diff", "--", "scripts/sync_all.ps1"], capture_output=True, text=True, check=False)
    assert completed.returncode == 0
    assert completed.stdout == ""
