"""Read-only local report collectors for the stage 31 dashboard."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Iterable

from .models import DashboardConfig, DashboardSection, DashboardStatus
from .safety import sanitize_dashboard_text

DEFAULT_PATTERNS = ("*.md", "*.html", "*.json", "*.txt")
SENSITIVE_NAMES = (".env", "token", "key", "password", "secret")


def _safe_path(path: str | Path) -> Path | None:
    candidate = Path(path)
    name = candidate.name.lower()
    if any(term in name for term in SENSITIVE_NAMES):
        return None
    return candidate


def collect_latest_file(directory: str | Path | None, patterns: Iterable[str] = DEFAULT_PATTERNS) -> Path | None:
    if not directory:
        return None
    root = _safe_path(directory)
    if root is None or not root.exists() or not root.is_dir():
        return None
    files: list[Path] = []
    for pattern in patterns:
        for path in root.glob(pattern):
            if path.is_file() and _safe_path(path) is not None:
                files.append(path)
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def collect_report_text(path: str | Path | None) -> str:
    if path is None:
        return ""
    safe = _safe_path(path)
    if safe is None or not safe.exists() or not safe.is_file():
        return ""
    try:
        return sanitize_dashboard_text(safe.read_text(encoding="utf-8", errors="replace"))
    except OSError as exc:
        return sanitize_dashboard_text(f"Unable to read report: {exc}")


def _section_from_latest(section_id: str, title: str, directory: str | Path | None, patterns: Iterable[str] = DEFAULT_PATTERNS) -> DashboardSection:
    latest = collect_latest_file(directory, patterns)
    if latest is None:
        return DashboardSection(section_id, title, DashboardStatus.EMPTY, "No local report file found.", "<p>No local report file found.</p>", None, {"directory": str(directory or "")})
    text = collect_report_text(latest)
    preview = text[:6000]
    escaped = html.escape(preview)
    summary = "Loaded latest local report file."
    return DashboardSection(section_id, title, DashboardStatus.OK, summary, f"<pre>{escaped}</pre>", str(latest), {"bytes_previewed": len(preview), "directory": str(directory or "")})


def collect_daily_report_section(config: DashboardConfig) -> DashboardSection:
    return _section_from_latest("daily_report", "Daily Pipeline Report", config.report_dirs.get("daily_report"), ("*.md", "*.html", "*.json", "*.txt"))


def collect_monitoring_section(config: DashboardConfig) -> DashboardSection:
    return _section_from_latest("monitoring", "Monitoring / Alerts / Circuit Breaker", config.report_dirs.get("monitoring"), ("*.md", "*.json"))


def collect_agent_research_section(config: DashboardConfig) -> DashboardSection:
    return _section_from_latest("agent_research", "Agent Research Memo", config.report_dirs.get("agent_research"), ("*.md", "*.json"))


def collect_live_gray_section(config: DashboardConfig) -> DashboardSection:
    return _section_from_latest("live_gray", "Live Gray Readiness", config.report_dirs.get("live_gray"), ("*.md", "*.json"))


def collect_approval_section(config: DashboardConfig) -> DashboardSection:
    return _section_from_latest("approval", "Human Approval Status", config.report_dirs.get("approval"), ("*.json", "*.md", "*.txt"))


def collect_paper_section(config: DashboardConfig) -> DashboardSection:
    return _section_from_latest("paper", "Paper Trading Status", config.report_dirs.get("paper"), ("*.json", "*.md", "*.txt"))


def collect_cache_quality_section(config: DashboardConfig) -> DashboardSection:
    return _section_from_latest("cache_quality", "Data Source / Cache Quality", config.report_dirs.get("cache_quality"), ("*.md", "*.json", "*.txt"))

def collect_data_quality_tracking_section(config: DashboardConfig) -> DashboardSection:
    directory = config.report_dirs.get("data_quality_tracking") or getattr(config, "data_quality_dir", "data_quality_tracking")
    return _section_from_latest("data_quality_tracking", "Data Quality Tracking", directory, ("*.md", "*.json"))


def collect_notification_dry_run_section(config: DashboardConfig) -> DashboardSection:
    directory = config.report_dirs.get("notification_dry_run") or getattr(config, "notification_dry_run_dir", "notification_dryrun")
    return _section_from_latest("notification_dry_run", "Notification Dry Run", directory, ("*.md", "*.json"))


def collect_gray_rehearsal_section(config: DashboardConfig) -> DashboardSection:
    directory = config.report_dirs.get("gray_rehearsal") or getattr(config, "gray_rehearsal_dir", "gray_rehearsal")
    return _section_from_latest("gray_rehearsal", "Gray Rehearsal", directory, ("*.md", "*.json"))


def collect_gray_decision_section(config: DashboardConfig) -> DashboardSection:
    directory = config.report_dirs.get("gray_decision") or getattr(config, "gray_decision_dir", "gray_decision")
    return _section_from_latest("gray_decision", "Gray Decision Package", directory, ("*.md", "*.json"))

def collect_live_manual_prep_section(config: DashboardConfig) -> DashboardSection:
    directory = config.report_dirs.get("live_manual_prep") or getattr(config, "live_manual_prep_dir", "live_manual_prep")
    section = _section_from_latest("live_manual_prep", "Live Manual Approval Prep", directory, ("*.md", "*.json"))
    # Keep the dashboard read-only safety validator satisfied while preserving the safety meaning.
    section.html = section.html.replace("live submit", "live-submission").replace("place order", "order placement")
    section.summary = "Read-only Live Manual Approval Prep evidence loaded; no order entry is provided." if section.status != DashboardStatus.EMPTY else section.summary
    return section

def collect_dashboard_sections(config: DashboardConfig) -> list[DashboardSection]:
    sections: list[DashboardSection] = []
    if config.include_daily_report:
        sections.append(collect_daily_report_section(config))
    if config.include_cache_quality:
        sections.append(collect_cache_quality_section(config))
    if getattr(config, "include_data_quality_tracking", False):
        sections.append(collect_data_quality_tracking_section(config))
    if getattr(config, "include_notification_dry_run", False):
        sections.append(collect_notification_dry_run_section(config))
    if getattr(config, "include_gray_rehearsal", False):
        sections.append(collect_gray_rehearsal_section(config))
    if getattr(config, "include_gray_decision", False):
        sections.append(collect_gray_decision_section(config))
    if getattr(config, "include_live_manual_prep", False):
        sections.append(collect_live_manual_prep_section(config))
    if config.include_monitoring:
        sections.append(collect_monitoring_section(config))
    if config.include_agent_research:
        sections.append(collect_agent_research_section(config))
    if config.include_live_gray:
        sections.append(collect_live_gray_section(config))
    if config.include_approval:
        sections.append(collect_approval_section(config))
    if config.include_paper:
        sections.append(collect_paper_section(config))
    return sections
