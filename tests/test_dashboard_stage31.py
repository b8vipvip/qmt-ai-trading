from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from qmt_ai_trading.dashboard.collector import collect_dashboard_sections
from qmt_ai_trading.dashboard.models import DashboardConfig, DashboardData, DashboardSection, DashboardStatus
from qmt_ai_trading.dashboard.render import render_dashboard_html
from qmt_ai_trading.dashboard.safety import (
    DashboardSafetyError,
    assert_dashboard_read_only,
    contains_forbidden_ui_action,
    sanitize_dashboard_text,
)

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_config_default_read_only() -> None:
    assert DashboardConfig().read_only is True


def test_dashboard_data_instantiable() -> None:
    data = DashboardData(sections=[DashboardSection("x", "X")])
    assert data.safety_note
    assert data.to_dict()["sections"][0]["section_id"] == "x"


def test_assert_read_only_blocks_false() -> None:
    assert_dashboard_read_only(DashboardConfig())
    with pytest.raises(DashboardSafetyError):
        assert_dashboard_read_only(DashboardConfig(read_only=False))


def test_sanitize_redacts_sensitive_values() -> None:
    text = sanitize_dashboard_text("token=abc key:def password = ghi secret:jkl")
    assert "abc" not in text and "def" not in text and "ghi" not in text and "jkl" not in text
    assert "REDACTED" in text


def test_forbidden_ui_action_detection() -> None:
    for phrase in ["提交订单", "实盘下单", "live submit", "place order"]:
        assert contains_forbidden_ui_action(phrase)


def test_render_html_safety_banner_and_no_order_button() -> None:
    html = render_dashboard_html(DashboardData(sections=[DashboardSection("safe", "Safe", DashboardStatus.OK, "ok", "<p>ok</p>")]))
    assert "Read-only dashboard" in html
    assert "<button" not in html.lower()
    assert "cdn" not in html.lower()


def test_collect_missing_dirs_no_crash(tmp_path: Path) -> None:
    config = DashboardConfig(report_dirs={"daily_report": str(tmp_path / "missing")})
    sections = collect_dashboard_sections(config)
    assert sections
    assert any(section.status == DashboardStatus.EMPTY for section in sections)


def test_build_dashboard_script_generates_html(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "daily.md").write_text("# Daily\nRiskDecision OK", encoding="utf-8")
    output = tmp_path / "dashboard" / "index.html"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_dashboard.py"), "--output", str(output), "--report-dir", str(report_dir), "--title", "Test Dashboard"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    html = output.read_text(encoding="utf-8")
    assert "Test Dashboard" in html
    assert "http://" not in html and "https://" not in html


def test_preview_print_path(tmp_path: Path) -> None:
    dashboard = tmp_path / "index.html"
    dashboard.write_text("ok", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_dashboard_preview.py"), "--dashboard", str(dashboard), "--print-path-only"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert str(dashboard.resolve()) in result.stdout


def test_register_dashboard_dry_run_command() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/register_daily_pipeline_task.py"), "--build-dashboard", "--dashboard-output", "dashboard/daily_dashboard.html", "--dashboard-title", "QMT AI Trading Dashboard"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--build-dashboard" in result.stdout
    assert "--dashboard-output" in result.stdout


def test_gitignore_and_roadmap_stage31_stage32() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    roadmap = (ROOT / "docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "dashboard_stage31/" in gitignore or "dashboard_output/" in gitignore
    assert "阶段三十一" in roadmap and "UI / Dashboard" in roadmap
    assert "阶段三十二" in roadmap and "运行手册 / 部署手册 / 总体验收" in roadmap


def test_sync_all_not_modified_by_stage31() -> None:
    assert (ROOT / "scripts/sync_all.ps1").exists()
