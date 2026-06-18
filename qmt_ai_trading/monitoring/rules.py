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
    if config.cache_coverage is not None:
        coverage = float(config.cache_coverage)
        if coverage < float(config.critical_cache_coverage):
            events.append(MonitoringEvent("cache_coverage_critical", "ERROR", f"Cache coverage {coverage:.2%} is below critical threshold {config.critical_cache_coverage:.2%}.", "cache_coverage", coverage, config.critical_cache_coverage, "CACHE"))
        elif coverage < float(config.min_cache_coverage):
            events.append(MonitoringEvent("cache_coverage_low", "WARNING", f"Cache coverage {coverage:.2%} is below threshold {config.min_cache_coverage:.2%}.", "cache_coverage", coverage, config.min_cache_coverage, "CACHE"))
    if config.fallback_used:
        events.append(MonitoringEvent("fallback_used", "WARNING", "Fallback/mock data path was used; do not treat the signal as live-ready.", "fallback_used", True, False, "DATA"))
    if int(config.risk_reject_count) > int(config.max_risk_reject_count):
        severity = "CRITICAL" if int(config.risk_reject_count) >= int(config.critical_risk_reject_count) else "ERROR"
        events.append(MonitoringEvent("risk_reject_spike", severity, f"Risk Gate rejected {config.risk_reject_count} intents, above threshold {config.max_risk_reject_count}.", "risk_reject_count", config.risk_reject_count, config.max_risk_reject_count, "RISK"))
    if int(config.scheduler_exit_code) != 0:
        events.append(MonitoringEvent("scheduler_failure", "CRITICAL", f"Scheduled pipeline exited with code {config.scheduler_exit_code}.", "scheduler_exit_code", config.scheduler_exit_code, 0, "SCHEDULER"))
    if float(config.max_drawdown) <= float(config.max_allowed_drawdown):
        severity = "CRITICAL" if float(config.max_drawdown) <= float(config.critical_max_drawdown) else "WARNING"
        events.append(MonitoringEvent("drawdown_breach", severity, f"Max drawdown {config.max_drawdown:.2%} breached threshold {config.max_allowed_drawdown:.2%}.", "max_drawdown", config.max_drawdown, config.max_allowed_drawdown, "BACKTEST"))
    return events


def detect_data_quality_tracking_events(report, config: MonitoringConfig) -> list[MonitoringEvent]:
    """Convert read-only DataQualityTrackingReport deterioration into monitoring events."""
    events: list[MonitoringEvent] = []
    threshold = float(getattr(config, "min_cache_coverage", 0.8))
    for incident in getattr(report, "incidents", []) or []:
        sev = str(getattr(incident, "severity", "WARNING")).upper()
        if sev in {"ERROR", "CRITICAL"}:
            events.append(MonitoringEvent("data_quality_tracking_incident", sev, getattr(incident, "message", "Data quality incident detected."), "incident", getattr(incident, "category", ""), sev, "QUALITY"))
    for trend in getattr(report, "trends", []) or []:
        level = str(getattr(trend, "trend_level", "UNKNOWN")).split(".")[-1].upper()
        avg = float(getattr(trend, "average_coverage", 0.0) or 0.0)
        if level == "FAIL":
            events.append(MonitoringEvent("data_quality_tracking_trend_fail", "ERROR", getattr(trend, "message", "Data quality trend failed."), "trend_level", level, "PASS", "QUALITY"))
        if avg < threshold:
            events.append(MonitoringEvent("data_quality_tracking_coverage_low", "WARNING", f"Data quality tracking average coverage {avg:.2%} below {threshold:.2%}.", "average_coverage", avg, threshold, "QUALITY"))
    return events
