from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from qmt_ai_trading.monitoring.service import MonitoringConfig, run_monitoring_check
from qmt_ai_trading.monitoring.formatters import format_monitoring_markdown
from qmt_ai_trading.scheduler.windows_task import build_daily_pipeline_command


def test_monitoring_circuit_breaker_and_alerts(tmp_path):
    report = run_monitoring_check(MonitoringConfig(quality_level="UNKNOWN", fallback_used=True, risk_reject_count=3, max_drawdown=-0.12, alert_output_dir=str(tmp_path), dry_run_alerts=True))
    assert report.circuit_breaker_triggered
    assert report.max_severity == "CRITICAL"
    assert {e.name for e in report.events} >= {"data_quality_warning", "fallback_used", "risk_reject_spike", "drawdown_breach"}
    assert report.alerts and all(Path(a["path"]).exists() for a in report.alerts)
    md = format_monitoring_markdown(report)
    assert "Monitoring Report" in md and "dry-run/paper only" in md


def test_monitoring_cli_outputs(tmp_path):
    md = tmp_path / "monitoring.md"; js = tmp_path / "monitoring.json"
    cp = subprocess.run([sys.executable, "scripts/run_monitoring_check.py", "--output", str(md), "--json-output", str(js), "--alert-output-dir", str(tmp_path / "alerts"), "--quality-level", "LOW", "--risk-reject-count", "3", "--max-drawdown", "-0.12"], cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True, timeout=60)
    assert cp.returncode == 0, cp.stderr + cp.stdout
    assert "Monitoring Report" in md.read_text(encoding="utf-8")
    data = json.loads(js.read_text(encoding="utf-8"))
    assert data["circuit_breaker_triggered"] is True


def test_scheduler_command_includes_monitoring_options():
    cmd = build_daily_pipeline_command(enable_monitoring=True, monitoring_output_dir="monitoring_reports_stage28", monitoring_dry_run_alerts=True)
    display = cmd.metadata["display"]
    assert "--enable-monitoring" in display
    assert "--monitoring-output-dir monitoring_reports_stage28" in display
    assert "--monitoring-dry-run-alerts" in display


def test_docs_and_gitignore_stage28():
    root = Path(__file__).resolve().parents[1]
    roadmap = (root / "docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    assert "阶段二十八" in roadmap and "异常监控、告警、熔断" in roadmap
    gi = (root / ".gitignore").read_text(encoding="utf-8")
    assert "monitoring_reports/" in gi and "alert_test_stage28/" in gi
