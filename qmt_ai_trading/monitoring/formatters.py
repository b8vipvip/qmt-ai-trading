"""Markdown formatters for monitoring reports."""
from __future__ import annotations
from .service import MonitoringReport


def format_monitoring_markdown(report: MonitoringReport) -> str:
    lines = [
        "# Monitoring Report",
        "",
        "Monitoring is dry-run/paper only; it does not submit orders or send real notifications.",
        "",
        f"- Run ID: `{report.run_id}`",
        f"- Generated at: `{report.generated_at}`",
        f"- Max severity: **{report.max_severity}**",
        f"- Circuit breaker triggered: **{report.circuit_breaker_triggered}**",
        f"- Dry-run alerts: **{len(report.alerts)} local file alert(s)**",
        "",
        "## Events",
        "",
        "| Severity | Event | Metric | Value | Threshold | Message |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for event in report.events:
        lines.append(f"| {event.severity} | {event.name} | {event.metric} | {event.value} | {event.threshold} | {event.message} |")
    if report.alerts:
        lines.extend(["", "## Dry-run alert files", ""])
        for alert in report.alerts:
            lines.append(f"- {alert.get('path')}")
    return "\n".join(lines) + "\n"


def format_monitoring_report_markdown(report: MonitoringReport) -> str:
    """Backward-compatible report formatter alias for Stage 28 acceptance tests."""
    return format_monitoring_markdown(report)
