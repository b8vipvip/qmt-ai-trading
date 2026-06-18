"""Dashboard build and save service."""

from __future__ import annotations

from pathlib import Path

from .collector import collect_dashboard_sections
from .models import DashboardConfig, DashboardData, DashboardStatus, SAFETY_NOTE
from .render import render_dashboard_html
from .safety import validate_dashboard_config


def build_dashboard(config: DashboardConfig) -> DashboardData:
    validate_dashboard_config(config)
    sections = collect_dashboard_sections(config)
    warnings = [f"{section.title}: {section.summary}" for section in sections if str(section.status) in {DashboardStatus.EMPTY.value, DashboardStatus.WARNING.value, DashboardStatus.ERROR.value}]
    return DashboardData(
        title=str(config.metadata.get("title", "QMT AI Trading Dashboard")),
        sections=sections,
        source_paths=[section.source_path for section in sections if section.source_path],
        warnings=warnings,
        safety_note=SAFETY_NOTE,
        metadata={"read_only": config.read_only, **config.metadata},
    )


def save_dashboard_html(data: DashboardData, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    html = render_dashboard_html(data)
    path.write_text(html, encoding="utf-8")
    return path


def build_and_save_dashboard(config: DashboardConfig) -> tuple[DashboardData, Path]:
    data = build_dashboard(config)
    return data, save_dashboard_html(data, config.output_path)


def preview_dashboard_path(output_path: str | Path) -> str:
    return str(Path(output_path).resolve())
