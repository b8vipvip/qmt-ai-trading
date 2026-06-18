"""Models for Stage 35 small-capital gray rehearsal."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

SAFETY_NOTE = "Gray rehearsal is dry-run only. It does not enable live trading, does not submit orders, does not send real notifications, and does not call xttrader or QMT trading APIs."

class GrayRehearsalDecision(str, Enum):
    PASS = "PASS"; WARN = "WARN"; FAIL = "FAIL"; BLOCKED = "BLOCKED"
class GrayRehearsalScenarioType(str, Enum):
    NORMAL_DRY_RUN = "NORMAL_DRY_RUN"; RISK_GATE_BLOCKED = "RISK_GATE_BLOCKED"; DATA_QUALITY_UNKNOWN = "DATA_QUALITY_UNKNOWN"; CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"; LIVE_GRAY_NO_GO = "LIVE_GRAY_NO_GO"; NOTIFICATION_DRY_RUN = "NOTIFICATION_DRY_RUN"; DASHBOARD_READ_ONLY = "DASHBOARD_READ_ONLY"
class GrayRehearsalStepStatus(str, Enum):
    PASS = "PASS"; WARN = "WARN"; FAIL = "FAIL"; SKIP = "SKIP"

def _default_scenarios() -> list[GrayRehearsalScenarioType]:
    return list(GrayRehearsalScenarioType)

def _enum(v: Any) -> Any:
    return v.value if isinstance(v, Enum) else v

def _clean(obj: Any) -> Any:
    if isinstance(obj, Enum): return obj.value
    if isinstance(obj, list): return [_clean(x) for x in obj]
    if isinstance(obj, dict): return {str(k): _clean(v) for k,v in obj.items()}
    return obj

@dataclass
class GrayRehearsalConfig:
    rehearsal_dry_run: bool = True
    scenario_types: list[GrayRehearsalScenarioType] = field(default_factory=_default_scenarios)
    allowed_symbols: list[str] = field(default_factory=list)
    max_total_capital: float = 5000.0
    max_single_order_value: float = 1000.0
    require_risk_gate: bool = True
    require_human_approval: bool = True
    require_paper_trading: bool = True
    require_monitoring: bool = True
    require_data_quality_tracking: bool = True
    require_agent_research: bool = True
    require_live_gray_readiness: bool = True
    require_notification_dry_run: bool = True
    require_dashboard: bool = True
    operator_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return _clean(asdict(self))

@dataclass
class GrayRehearsalStep:
    step_id: str
    scenario_type: GrayRehearsalScenarioType | str
    title: str
    status: GrayRehearsalStepStatus | str
    message: str = ""
    evidence: list[str] = field(default_factory=list)
    remediation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return _clean(asdict(self))

@dataclass
class GrayRehearsalScenarioResult:
    scenario_id: str
    scenario_type: GrayRehearsalScenarioType | str
    title: str
    decision: GrayRehearsalDecision | str
    steps: list[GrayRehearsalStep] = field(default_factory=list)
    summary: str = ""
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return {**_clean(asdict(self)), "steps":[s.to_dict() for s in self.steps]}

@dataclass
class GrayRehearsalReport:
    report_id: str = field(default_factory=lambda: f"gray-rehearsal-{uuid4().hex[:12]}")
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: GrayRehearsalDecision | str = GrayRehearsalDecision.WARN
    config: GrayRehearsalConfig = field(default_factory=GrayRehearsalConfig)
    scenarios: list[GrayRehearsalScenarioResult] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)
    summary: str = ""
    safety_note: str = SAFETY_NOTE
    success: bool = True
    message: str = "Dry-run rehearsal only; not live authorization."
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]:
        return {"report_id":self.report_id,"created_at":self.created_at,"decision":_enum(self.decision),"config":self.config.to_dict(),"scenarios":[s.to_dict() for s in self.scenarios],"checklist":list(self.checklist),"summary":self.summary,"safety_note":self.safety_note,"success":bool(self.success),"message":self.message,"metadata":_clean(self.metadata)}
