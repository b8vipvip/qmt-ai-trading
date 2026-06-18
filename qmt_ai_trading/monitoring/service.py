"""Monitoring checks for the dry-run QMT AI Trading pipeline.

The monitor is intentionally non-trading: it emits events, dry-run alerts and a
circuit-breaker recommendation, but it never calls QMT, xttrader, notification
providers, or order APIs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .circuit_breaker import decide_circuit_breaker
from .models import (
    ALERT_LEVELS,
    CIRCUIT_BREAKER_STATES,
    MONITORING_CATEGORIES,
    SEVERITY_ORDER,
    Alert,
    CircuitBreakerDecision,
    MonitoringConfig,
    MonitoringEvent,
    MonitoringReport,
)
from .notifier import write_dry_run_alerts
from .rules import evaluate_monitoring_rules, max_severity


def _max_severity(events: Iterable[MonitoringEvent]) -> str:
    """Backward-compatible alias for older imports/tests."""
    return max_severity(events)


def _write_alerts(report: MonitoringReport, output_dir: str | Path | None) -> list[dict[str, object]]:
    """Backward-compatible alias for older imports/tests."""
    return write_dry_run_alerts(report, output_dir)


def run_monitoring_check(config: MonitoringConfig | None = None, *, run_id: str | None = None) -> MonitoringReport:
    cfg = config or MonitoringConfig()
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rid = run_id or f"monitoring-{now}"
    events = evaluate_monitoring_rules(cfg)
    generated_at = datetime.now(timezone.utc).isoformat()
    decision = decide_circuit_breaker(events)
    report = MonitoringReport(
        rid,
        generated_at,
        True,
        decision.triggered,
        decision.max_severity,
        events,
        [],
        True,
        dict(cfg.metadata),
        decision,
    )
    if cfg.dry_run_alerts:
        report.alerts = write_dry_run_alerts(report, cfg.alert_output_dir)
    return report


def save_monitoring_json(report: MonitoringReport, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
