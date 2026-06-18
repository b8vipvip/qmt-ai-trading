"""Dry-run circuit-breaker decisions for monitoring reports."""

from __future__ import annotations

from collections.abc import Iterable

from .models import CircuitBreakerDecision, MonitoringEvent
from .rules import max_severity


def decide_circuit_breaker(events: Iterable[MonitoringEvent]) -> CircuitBreakerDecision:
    event_list = list(events)
    severity = max_severity(event_list)
    if severity == "CRITICAL":
        critical_names = ", ".join(event.name for event in event_list if event.severity == "CRITICAL")
        return CircuitBreakerDecision("OPEN", True, f"Critical monitoring event(s): {critical_names}", severity)
    if severity in {"WARNING", "ERROR"}:
        return CircuitBreakerDecision("HALF_OPEN", False, "Warnings require human review before live readiness.", severity)
    return CircuitBreakerDecision("CLOSED", False, "No blocking monitoring events detected.", severity)
