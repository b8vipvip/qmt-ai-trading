"""Rule evaluation for Stage 28 dry-run monitoring."""

from __future__ import annotations

from collections.abc import Iterable

from .models import MonitoringConfig, MonitoringEvent, SEVERITY_ORDER


def max_severity(events: Iterable[MonitoringEvent]) -> str:
    severity = "INFO"
    for event in events:
        if SEVERITY_ORDER.get(event.severity, 0) > SEVERITY_ORDER.get(severity, 0):
            severity = event.severity
    return severity


def evaluate_monitoring_rules(config: MonitoringConfig) -> list[MonitoringEvent]:
    events: list[MonitoringEvent] = [
        MonitoringEvent(
            "monitoring_started",
            "INFO",
            "Monitoring check executed in dry-run mode.",
            category="SYSTEM",
        )
    ]
    quality = str(config.quality_level or "UNKNOWN").upper()
    if quality in {"UNKNOWN", "LOW", "UNAVAILABLE"}:
        events.append(
            MonitoringEvent(
                "data_quality_warning",
                "WARNING",
                f"Data quality level is {quality}; keep strategy in dry-run/paper review.",
                "quality_level",
                quality,
                "MEDIUM",
                "QUALITY",
            )
        )
    if config.fallback_used:
        events.append(MonitoringEvent("fallback_used", "WARNING", "Fallback/mock data path was used; do not treat the signal as live-ready.", "fallback_used", True, False, "DATA"))
    if int(config.risk_reject_count) > int(config.max_risk_reject_count):
        events.append(MonitoringEvent("risk_reject_spike", "CRITICAL", f"Risk Gate rejected {config.risk_reject_count} intents, above threshold {config.max_risk_reject_count}.", "risk_reject_count", config.risk_reject_count, config.max_risk_reject_count, "RISK"))
    if int(config.scheduler_exit_code) != 0:
        events.append(MonitoringEvent("scheduler_failure", "CRITICAL", f"Scheduled pipeline exited with code {config.scheduler_exit_code}.", "scheduler_exit_code", config.scheduler_exit_code, 0, "SCHEDULER"))
    if float(config.max_drawdown) <= float(config.max_allowed_drawdown):
        events.append(MonitoringEvent("drawdown_breach", "CRITICAL", f"Max drawdown {config.max_drawdown:.2%} breached threshold {config.max_allowed_drawdown:.2%}.", "max_drawdown", config.max_drawdown, config.max_allowed_drawdown, "BACKTEST"))
    return events
