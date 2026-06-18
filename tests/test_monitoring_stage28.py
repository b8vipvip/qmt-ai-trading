from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from qmt_ai_trading.monitoring.circuit_breaker import decide_circuit_breaker
from qmt_ai_trading.monitoring.formatters import (
    format_monitoring_markdown,
    format_monitoring_report_markdown,
)
from qmt_ai_trading.monitoring.models import Alert, CircuitBreakerDecision, MonitoringEvent
from qmt_ai_trading.monitoring.notifier import write_dry_run_alerts
from qmt_ai_trading.monitoring.rules import evaluate_monitoring_rules
from qmt_ai_trading.monitoring.service import MonitoringConfig, MonitoringReport, run_monitoring_check
from qmt_ai_trading.scheduler.windows_task import build_daily_pipeline_command

ROOT = Path(__file__).resolve().parents[1]
SYNC_ALL = ROOT / "scripts/sync_all.ps1"


def _run(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout)


def _event_by_name(events: list[MonitoringEvent], name: str) -> MonitoringEvent:
    matches = [event for event in events if event.name == name]
    assert matches, f"missing monitoring event {name}; got {[event.name for event in events]}"
    return matches[0]


def test_monitoring_models_are_instantiable():
    event = MonitoringEvent("cache_coverage_warning", "WARNING", "cache coverage is low", "cache_coverage", 0.5, 0.8, "CACHE")
    alert = Alert("run-1", "WARNING", event.name, event.message, "2026-06-18T00:00:00Z", dry_run=True)
    decision = CircuitBreakerDecision("OPEN", True, "critical event", "CRITICAL")

    assert event.category == "CACHE"
    assert alert.dry_run is True
    assert alert.real_notification_sent is False
    assert decision.state == "OPEN"
    assert decision.dry_run_only is True


def test_low_cache_coverage_generates_warning_and_error():
    warning_events = evaluate_monitoring_rules(MonitoringConfig(cache_coverage=0.75, min_cache_coverage=0.8, critical_cache_coverage=0.5))
    error_events = evaluate_monitoring_rules(MonitoringConfig(cache_coverage=0.25, min_cache_coverage=0.8, critical_cache_coverage=0.5))

    assert _event_by_name(warning_events, "cache_coverage_low").severity == "WARNING"
    assert _event_by_name(error_events, "cache_coverage_critical").severity == "ERROR"


def test_unknown_and_low_quality_generate_warning():
    for level in ("UNKNOWN", "LOW"):
        events = evaluate_monitoring_rules(MonitoringConfig(quality_level=level))
        event = _event_by_name(events, "data_quality_warning")
        assert event.severity == "WARNING"
        assert event.value == level


def test_risk_reject_count_thresholds_generate_error_and_critical():
    error_events = evaluate_monitoring_rules(MonitoringConfig(risk_reject_count=2, max_risk_reject_count=1, critical_risk_reject_count=3))
    critical_events = evaluate_monitoring_rules(MonitoringConfig(risk_reject_count=4, max_risk_reject_count=1, critical_risk_reject_count=3))

    assert _event_by_name(error_events, "risk_reject_spike").severity == "ERROR"
    assert _event_by_name(critical_events, "risk_reject_spike").severity == "CRITICAL"


def test_drawdown_thresholds_generate_warning_and_critical():
    warning_events = evaluate_monitoring_rules(MonitoringConfig(max_drawdown=-0.08, max_allowed_drawdown=-0.05, critical_max_drawdown=-0.10))
    critical_events = evaluate_monitoring_rules(MonitoringConfig(max_drawdown=-0.12, max_allowed_drawdown=-0.05, critical_max_drawdown=-0.10))

    assert _event_by_name(warning_events, "drawdown_breach").severity == "WARNING"
    assert _event_by_name(critical_events, "drawdown_breach").severity == "CRITICAL"


def test_critical_event_opens_circuit_breaker():
    decision = decide_circuit_breaker([MonitoringEvent("scheduler_failure", "CRITICAL", "failed")])

    assert decision.state == "OPEN"
    assert decision.triggered is True
    assert decision.max_severity == "CRITICAL"


def test_dry_run_alert_writes_local_files_without_external_notification(tmp_path):
    report = MonitoringReport(
        "run-1",
        "2026-06-18T00:00:00Z",
        True,
        False,
        "WARNING",
        [MonitoringEvent("data_quality_warning", "WARNING", "quality warning")],
    )

    alerts = write_dry_run_alerts(report, tmp_path)
    payload = json.loads(Path(alerts[0]["path"]).read_text(encoding="utf-8"))

    assert len(alerts) == 1
    assert payload["dry_run"] is True
    assert payload["channel"] == "local_file"
    assert payload["real_notification_sent"] is False


def test_monitoring_circuit_breaker_and_alerts(tmp_path):
    report = run_monitoring_check(MonitoringConfig(quality_level="UNKNOWN", fallback_used=True, risk_reject_count=3, max_drawdown=-0.12, alert_output_dir=str(tmp_path), dry_run_alerts=True))
    assert report.circuit_breaker_triggered
    assert report.circuit_breaker and report.circuit_breaker.state == "OPEN"
    assert report.max_severity == "CRITICAL"
    assert {e.name for e in report.events} >= {"data_quality_warning", "fallback_used", "risk_reject_spike", "drawdown_breach"}
    assert report.alerts and all(Path(a["path"]).exists() for a in report.alerts)


def test_format_monitoring_report_markdown_contains_safety_notice():
    report = run_monitoring_check(MonitoringConfig(quality_level="HIGH", dry_run_alerts=True))
    md = format_monitoring_report_markdown(report)

    assert "Monitoring Report" in md
    assert "dry-run/paper only" in md
    assert "does not submit orders" in md
    assert "send real notifications" in md


def test_monitoring_cli_outputs(tmp_path):
    md = tmp_path / "monitoring.md"
    js = tmp_path / "monitoring.json"
    cp = _run([sys.executable, "scripts/run_monitoring_check.py", "--output", str(md), "--json-output", str(js), "--alert-output-dir", str(tmp_path / "alerts"), "--quality-level", "LOW", "--risk-reject-count", "3", "--max-drawdown", "-0.12", "--dry-run-alerts"])
    assert cp.returncode == 0, cp.stderr + cp.stdout
    assert "Monitoring Report" in md.read_text(encoding="utf-8")
    data = json.loads(js.read_text(encoding="utf-8"))
    assert data["circuit_breaker_triggered"] is True


def test_daily_pipeline_enable_monitoring_outputs_report(tmp_path):
    cp = _run([
        sys.executable, "scripts/run_daily_pipeline.py",
        "--cache-root", str(tmp_path / "market_data"),
        "--research-start", "2026-05-09", "--research-end", "2026-06-18", "--research-frequency", "1d",
        "--min-bars", "20", "--cached-strategy-top-n", "2",
        "--enable-portfolio-plan", "--portfolio-method", "score_weight", "--portfolio-top-n", "2",
        "--portfolio-total-asset", "1000000", "--portfolio-cash-reserve-ratio", "0.2",
        "--portfolio-max-symbol-weight", "0.3", "--portfolio-max-weight", "0.8",
        "--enable-monitoring", "--monitoring-output-dir", str(tmp_path / "monitoring_reports"), "--monitoring-dry-run-alerts",
    ], timeout=180)

    assert cp.returncode == 0, cp.stderr + cp.stdout
    assert "Monitoring Report" in cp.stdout
    assert (tmp_path / "monitoring_reports" / "monitoring.md").exists()
    assert (tmp_path / "monitoring_reports" / "monitoring.json").exists()


def test_scheduled_pipeline_enable_monitoring_runs(tmp_path):
    cp = _run([sys.executable, "scripts/run_scheduled_daily_pipeline.py", "--cache-root", str(tmp_path / "market_data"), "--report-dir", str(tmp_path / "reports"), "--enable-monitoring", "--monitoring-output-dir", str(tmp_path / "monitoring_reports"), "--monitoring-dry-run-alerts"], timeout=180)
    assert cp.returncode == 0, cp.stderr + cp.stdout


def test_register_task_and_scheduler_command_include_monitoring_options(tmp_path):
    cmd = build_daily_pipeline_command(enable_monitoring=True, monitoring_output_dir="monitoring_reports_stage28", monitoring_dry_run_alerts=True)
    display = cmd.metadata["display"]
    assert "--enable-monitoring" in display
    assert "--monitoring-output-dir monitoring_reports_stage28" in display
    assert "--monitoring-dry-run-alerts" in display

    cp = _run([sys.executable, "scripts/register_daily_pipeline_task.py", "--enable-monitoring", "--monitoring-output-dir", str(tmp_path / "monitoring_reports"), "--monitoring-dry-run-alerts"])
    assert cp.returncode == 0, cp.stderr + cp.stdout
    assert "DRY-RUN ONLY" in cp.stdout
    assert "--enable-monitoring" in cp.stdout
    assert "--monitoring-output-dir" in cp.stdout
    assert "--monitoring-dry-run-alerts" in cp.stdout


def test_roadmap_architecture_gitignore_and_sync_all_stage28_stage29():
    roadmap = (ROOT / "docs/qmt-ai-trading-project-roadmap.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs/qmt-ai-trading-architecture.md").read_text(encoding="utf-8")
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    sync_before = SYNC_ALL.read_bytes()

    assert "阶段二十八" in roadmap and "异常监控、告警、熔断" in roadmap and "已完成" in roadmap
    assert "阶段二十九" in roadmap and "Agent Research Layer" in roadmap
    assert "先读本 roadmap" in roadmap and "architecture" in roadmap and "最近阶段文档" in roadmap
    assert "阶段二十八" in architecture and "Monitoring" in architecture
    assert "Pipeline / Backtest / Scheduler" in architecture
    assert "dry-run" in architecture and "不真实发送通知" in architecture
    assert "xttrader" in architecture and "不真实下单" in architecture
    assert "monitoring_reports/" in gi and "alert_test_stage28/" in gi
    assert SYNC_ALL.read_bytes() == sync_before
