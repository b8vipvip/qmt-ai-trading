"""Data models for Stage 28 monitoring.

All models in this module are dry-run/paper-only. They describe monitoring
state, alert payloads, and circuit-breaker recommendations without calling QMT,
xttrader, notification providers, or order APIs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

MONITORING_CATEGORIES = (
    "DATA",
    "CACHE",
    "QUALITY",
    "SIGNAL",
    "RISK",
    "BACKTEST",
    "SCHEDULER",
    "APPROVAL",
    "PAPER",
    "SYSTEM",
)

ALERT_LEVELS = ("INFO", "WARNING", "ERROR", "CRITICAL")
SEVERITY_ORDER = {"INFO": 0, "WARNING": 1, "ERROR": 2, "CRITICAL": 3}
CIRCUIT_BREAKER_STATES = ("OPEN", "HALF_OPEN", "CLOSED")


@dataclass
class MonitoringEvent:
    name: str
    severity: str
    message: str
    metric: str = ""
    value: Any = None
    threshold: Any = None
    category: str = "SYSTEM"


@dataclass
class Alert:
    run_id: str
    severity: str
    event: str
    message: str
    created_at: str
    dry_run: bool = True
    channel: str = "local_file"
    real_notification_sent: bool = False
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


@dataclass
class CircuitBreakerDecision:
    state: str
    triggered: bool
    reason: str
    max_severity: str
    dry_run_only: bool = True


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
    circuit_breaker: CircuitBreakerDecision | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["events"] = [asdict(item) for item in self.events]
        return data
