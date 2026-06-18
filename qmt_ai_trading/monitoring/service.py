"""Monitoring checks for the dry-run QMT AI Trading pipeline.

The monitor is intentionally non-trading: it emits events, dry-run alerts and a
circuit-breaker recommendation, but it never calls QMT or order APIs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import json

SEVERITY_ORDER = {"INFO": 0, "WARNING": 1, "CRITICAL": 2}


@dataclass
class MonitoringEvent:
    name: str
    severity: str
    message: str
    metric: str = ""
    value: Any = None
    threshold: Any = None


@dataclass
class MonitoringConfig:
    quality_level: str = "UNKNOWN"
    fallback_used: bool = False
    risk_reject_count: int = 0
    scheduler_exit_code: int = 0
    max_drawdown: float = 0.0
    max_risk_reject_count: int = 2
    max_allowed_drawdown: float = -0.10
    dry_run_alerts: bool = True
    alert_output_dir: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringReport:
    run_id: str
    generated_at: str
    success: bool
    circuit_breaker_triggered: bool
    max_severity: str
    events: list[MonitoringEvent] = field(default_factory=list)
    alerts: list[dict[str, Any]] = field(default_factory=list)
    dry_run_only: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["events"] = [asdict(item) for item in self.events]
        return data


def _max_severity(events: Iterable[MonitoringEvent]) -> str:
    severity = "INFO"
    for event in events:
        if SEVERITY_ORDER.get(event.severity, 0) > SEVERITY_ORDER.get(severity, 0):
            severity = event.severity
    return severity


def _write_alerts(report: MonitoringReport, output_dir: str | Path | None) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if not output_dir:
        return alerts
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    for idx, event in enumerate(report.events, start=1):
        if event.severity == "INFO":
            continue
        payload = {
            "run_id": report.run_id,
            "dry_run": True,
            "channel": "local_file",
            "severity": event.severity,
            "event": event.name,
            "message": event.message,
            "created_at": report.generated_at,
            "real_notification_sent": False,
        }
        path = root / f"{report.run_id}.{idx}.{event.name}.alert.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["path"] = str(path)
        alerts.append(payload)
    return alerts


def run_monitoring_check(config: MonitoringConfig | None = None, *, run_id: str | None = None) -> MonitoringReport:
    cfg = config or MonitoringConfig()
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rid = run_id or f"monitoring-{now}"
    events: list[MonitoringEvent] = [MonitoringEvent("monitoring_started", "INFO", "Monitoring check executed in dry-run mode.")]
    quality = str(cfg.quality_level or "UNKNOWN").upper()
    if quality in {"UNKNOWN", "LOW", "UNAVAILABLE"}:
        events.append(MonitoringEvent("data_quality_warning", "WARNING", f"Data quality level is {quality}; keep strategy in dry-run/paper review.", "quality_level", quality, "MEDIUM"))
    if cfg.fallback_used:
        events.append(MonitoringEvent("fallback_used", "WARNING", "Fallback/mock data path was used; do not treat the signal as live-ready.", "fallback_used", True, False))
    if int(cfg.risk_reject_count) > int(cfg.max_risk_reject_count):
        events.append(MonitoringEvent("risk_reject_spike", "CRITICAL", f"Risk Gate rejected {cfg.risk_reject_count} intents, above threshold {cfg.max_risk_reject_count}.", "risk_reject_count", cfg.risk_reject_count, cfg.max_risk_reject_count))
    if int(cfg.scheduler_exit_code) != 0:
        events.append(MonitoringEvent("scheduler_failure", "CRITICAL", f"Scheduled pipeline exited with code {cfg.scheduler_exit_code}.", "scheduler_exit_code", cfg.scheduler_exit_code, 0))
    if float(cfg.max_drawdown) <= float(cfg.max_allowed_drawdown):
        events.append(MonitoringEvent("drawdown_breach", "CRITICAL", f"Max drawdown {cfg.max_drawdown:.2%} breached threshold {cfg.max_allowed_drawdown:.2%}.", "max_drawdown", cfg.max_drawdown, cfg.max_allowed_drawdown))
    severity = _max_severity(events)
    report = MonitoringReport(rid, datetime.now(timezone.utc).isoformat(), True, severity == "CRITICAL", severity, events, [], True, dict(cfg.metadata))
    if cfg.dry_run_alerts:
        report.alerts = _write_alerts(report, cfg.alert_output_dir)
    return report


def save_monitoring_json(report: MonitoringReport, path: str | Path) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
