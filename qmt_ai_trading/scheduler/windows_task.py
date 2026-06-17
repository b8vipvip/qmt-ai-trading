"""Windows Task Scheduler helpers for the dry-run daily pipeline.

The defaults are intentionally safe: functions return command previews and do not
call ``schtasks`` unless ``dry_run=False`` is explicitly requested.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .models import ScheduleCommand, ScheduleConfig, ScheduleResult

DEFAULT_TASK_NAME = "QmtAiTradingDailyDryRun"
DEFAULT_RUN_TIME = "15:30"


def _quote_for_display(value: str | Path) -> str:
    text = str(value)
    escaped = text.replace('"', '\\"')
    return f'"{escaped}"' if any(ch.isspace() for ch in escaped) else escaped


def _project_root(project_root: str | Path | None = None) -> Path:
    return Path(project_root).resolve() if project_root else Path.cwd().resolve()


def build_daily_pipeline_command(
    *,
    project_root: str | Path | None = None,
    python_command: str = "py",
    script_path: str | Path = Path("scripts/run_daily_pipeline.py"),
    report_dir: str | Path = Path("reports"),
    write_reports: bool = True,
    notify_dry_run: bool = True,
    warmup_cache: bool = False,
    warmup_provider: str = "mock",
    warmup_start: str | None = None,
    warmup_end: str | None = None,
    warmup_frequency: str = "1d",
    cache_root: str | Path = Path("market_data"),
) -> ScheduleCommand:
    """Build the safe daily pipeline command used by the scheduled task."""

    args = [str(script_path)]
    if warmup_cache:
        args.append("--warmup-cache")
        args.extend(["--warmup-provider", str(warmup_provider)])
        if warmup_start:
            args.extend(["--warmup-start", str(warmup_start)])
        if warmup_end:
            args.extend(["--warmup-end", str(warmup_end)])
        args.extend(["--warmup-frequency", str(warmup_frequency)])
        args.extend(["--cache-root", str(cache_root)])
    if write_reports:
        args.append("--write-reports")
    args.extend(["--report-dir", str(report_dir)])
    if notify_dry_run:
        args.append("--notify-dry-run")
    display = " ".join([_quote_for_display(python_command), *[_quote_for_display(arg) for arg in args]])
    return ScheduleCommand(
        command=str(python_command),
        arguments=args,
        working_directory=_project_root(project_root),
        description="Run the QMT AI Trading daily pipeline in dry-run/shadow mode.",
        metadata={"display": display, "safe_mode": "dry-run/shadow", "real_notifications": False, "real_orders": False},
    )


def build_schtasks_create_command(config: ScheduleConfig | None = None, **overrides: object) -> ScheduleCommand:
    """Build a ``schtasks /Create`` command preview for the daily dry-run task."""

    cfg = config or ScheduleConfig()
    for key, value in overrides.items():
        if value is not None and hasattr(cfg, key):
            setattr(cfg, key, value)
    project_root = _project_root(cfg.project_root)
    pipeline = build_daily_pipeline_command(
        project_root=project_root,
        python_command=cfg.python_command,
        script_path=cfg.script_path,
        report_dir=cfg.report_dir,
        write_reports=cfg.write_reports,
        notify_dry_run=cfg.notify_dry_run,
        warmup_cache=cfg.warmup_cache,
        warmup_provider=cfg.warmup_provider,
        warmup_start=cfg.warmup_start,
        warmup_end=cfg.warmup_end,
        warmup_frequency=cfg.warmup_frequency,
        cache_root=cfg.cache_root,
    )
    task_run = pipeline.metadata["display"]
    args = ["/Create", "/F", "/SC", "DAILY", "/TN", cfg.task_name, "/TR", task_run, "/ST", cfg.run_time]
    display = " ".join(["schtasks", *[_quote_for_display(arg) for arg in args]])
    return ScheduleCommand("schtasks", args, project_root, "Create Windows scheduled task for dry-run daily pipeline.", {"display": display, "task_run": task_run})


def build_schtasks_delete_command(task_name: str = DEFAULT_TASK_NAME, project_root: str | Path | None = None) -> ScheduleCommand:
    args = ["/Delete", "/F", "/TN", task_name]
    display = " ".join(["schtasks", *[_quote_for_display(arg) for arg in args]])
    return ScheduleCommand("schtasks", args, _project_root(project_root), "Delete Windows scheduled task.", {"display": display})


def build_schtasks_query_command(task_name: str = DEFAULT_TASK_NAME, project_root: str | Path | None = None) -> ScheduleCommand:
    args = ["/Query", "/TN", task_name]
    display = " ".join(["schtasks", *[_quote_for_display(arg) for arg in args]])
    return ScheduleCommand("schtasks", args, _project_root(project_root), "Query Windows scheduled task.", {"display": display})


def _run_command(command: ScheduleCommand) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [command.command, *command.arguments],
        cwd=command.working_directory,
        check=False,
        capture_output=True,
        text=True,
    )


def register_windows_task(config: ScheduleConfig | None = None, *, dry_run: bool = True, **overrides: object) -> ScheduleResult:
    command = build_schtasks_create_command(config, **overrides)
    if dry_run:
        return ScheduleResult(True, True, "dry-run only; no task registered", command, {"executed": False})
    completed = _run_command(command)
    return ScheduleResult(completed.returncode == 0, False, completed.stdout.strip() or completed.stderr.strip(), command, {"returncode": completed.returncode})


def unregister_windows_task(task_name: str = DEFAULT_TASK_NAME, *, project_root: str | Path | None = None, dry_run: bool = True) -> ScheduleResult:
    command = build_schtasks_delete_command(task_name, project_root)
    if dry_run:
        return ScheduleResult(True, True, "dry-run only; no task deleted", command, {"executed": False})
    completed = _run_command(command)
    return ScheduleResult(completed.returncode == 0, False, completed.stdout.strip() or completed.stderr.strip(), command, {"returncode": completed.returncode})


def query_windows_task(task_name: str = DEFAULT_TASK_NAME, *, project_root: str | Path | None = None, dry_run: bool = True) -> ScheduleResult:
    command = build_schtasks_query_command(task_name, project_root)
    if dry_run:
        return ScheduleResult(True, True, "dry-run only; no task queried", command, {"executed": False})
    completed = _run_command(command)
    return ScheduleResult(completed.returncode == 0, False, completed.stdout.strip() or completed.stderr.strip(), command, {"returncode": completed.returncode})
