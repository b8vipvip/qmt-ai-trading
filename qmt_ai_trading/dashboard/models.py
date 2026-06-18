"""Models for the local read-only stage 31 dashboard."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SAFETY_NOTE = "Read-only dashboard. This is not an order entry system. It cannot submit orders or bypass Risk Gate, Human Approval, Live Readiness Audit, Monitoring, or Circuit Breaker."


class DashboardStatus(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"
    EMPTY = "EMPTY"


@dataclass
class DashboardSection:
    section_id: str
    title: str
    status: DashboardStatus | str = DashboardStatus.EMPTY
    summary: str = ""
    html: str = ""
    source_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value if isinstance(self.status, DashboardStatus) else str(self.status)
        return data


@dataclass
class DashboardData:
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    title: str = "QMT AI Trading Dashboard"
    sections: list[DashboardSection] = field(default_factory=list)
    source_paths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    safety_note: str = SAFETY_NOTE
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "title": self.title,
            "sections": [section.to_dict() for section in self.sections],
            "source_paths": list(self.source_paths),
            "warnings": list(self.warnings),
            "safety_note": self.safety_note,
            "metadata": dict(self.metadata),
        }


@dataclass
class DashboardConfig:
    report_dirs: dict[str, str] = field(default_factory=dict)
    output_path: str = "dashboard_stage31/index.html"
    include_daily_report: bool = True
    include_monitoring: bool = True
    include_agent_research: bool = True
    include_live_gray: bool = True
    include_approval: bool = True
    include_paper: bool = True
    include_cache_quality: bool = True
    include_data_quality_tracking: bool = False
    data_quality_dir: str = "data_quality_tracking"
    include_notification_dry_run: bool = False
    notification_dry_run_dir: str = "notification_dryrun"
    include_gray_rehearsal: bool = False
    gray_rehearsal_dir: str = "gray_rehearsal"
    include_gray_decision: bool = False
    gray_decision_dir: str = "gray_decision"
    read_only: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
