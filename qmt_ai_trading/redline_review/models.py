from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

SAFETY_NOTE = "Red-line review is review-only and dry-run. It does not enable live trading, does not submit orders, does not send real notifications, and does not call xttrader or QMT trading APIs."
class RedlineReviewDecision(str, Enum):
    BLOCKED="BLOCKED"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_REDLINE_REVIEW="READY_FOR_REDLINE_REVIEW"
class RedlineSeverity(str, Enum): INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class RedlineStatus(str, Enum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"
class RedlineCategory(str, Enum):
    LIVE_SWITCH="LIVE_SWITCH"; EXECUTE_SWITCH="EXECUTE_SWITCH"; REAL_NOTIFICATION="REAL_NOTIFICATION"; QMT_TRADING_API="QMT_TRADING_API"; XTTRADER="XTTRADER"; ACCOUNT_QUERY="ACCOUNT_QUERY"; ORDER_SUBMISSION="ORDER_SUBMISSION"; RISK_BYPASS="RISK_BYPASS"; APPROVAL_BYPASS="APPROVAL_BYPASS"; SCHEDULER="SCHEDULER"; DASHBOARD="DASHBOARD"; DOCUMENTATION="DOCUMENTATION"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v: Any) -> str: return v.value if isinstance(v, Enum) else str(v)
@dataclass
class RedlineReviewConfig:
    repo_root: str = "."
    include_paths: list[str] = field(default_factory=lambda:["qmt_ai_trading","scripts","docs","tests"])
    exclude_paths: list[str] = field(default_factory=lambda:[".git","__pycache__",".pytest_cache",".venv","venv","market_data","data_cache","reports","logs","approvals","paper_orders","final_authorization_stage39","final_authorization_stage40","redline_review_stage40","dashboard_stage40","monitoring_reports_stage40"])
    allowed_live_markers: list[str] = field(default_factory=list)
    allowed_dry_run_markers: list[str] = field(default_factory=list)
    require_scheduler_dry_run: bool = True
    require_dashboard_read_only: bool = True
    require_no_sensitive_files: bool = True
    require_no_xttrader: bool = True
    require_no_qmt_trading_api: bool = True
    require_no_account_queries: bool = True
    require_no_real_notifications: bool = True
    require_no_execute_live: bool = True
    operator_name: str = ""
    reviewer_name: str = ""
    metadata: dict[str, Any] = field(default_factory=lambda:{"review_only": True, "live_enabled": False, "execute_live": False, "real_send_enabled": False, "external_network_enabled": False})
    def to_dict(self)->dict[str,Any]: return asdict(self)
@dataclass
class RedlineFinding:
    finding_id: str
    category: RedlineCategory | str
    status: RedlineStatus | str
    severity: RedlineSeverity | str
    path: str = ""
    line_number: int | None = None
    marker: str = ""
    message: str = ""
    remediation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self)->dict[str,Any]:
        d=asdict(self); d["category"]=enum_value(self.category); d["status"]=enum_value(self.status); d["severity"]=enum_value(self.severity); return d
@dataclass
class RedlineReviewReport:
    report_id: str = field(default_factory=lambda:f"redline-review-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}")
    created_at: str = field(default_factory=lambda:datetime.now(timezone.utc).isoformat())
    decision: RedlineReviewDecision | str = RedlineReviewDecision.NEED_MORE_EVIDENCE
    config: RedlineReviewConfig = field(default_factory=RedlineReviewConfig)
    findings: list[RedlineFinding] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: str = "Live switch isolation and red-line review summary."
    safety_note: str = SAFETY_NOTE
    success: bool = True
    message: str = "Generated review-only red-line review report."
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self)->dict[str,Any]:
        return {"report_id":self.report_id,"created_at":self.created_at,"decision":enum_value(self.decision),"config":self.config.to_dict(),"findings":[f.to_dict() for f in self.findings],"blocked_reasons":list(dict.fromkeys(self.blocked_reasons)),"warnings":list(dict.fromkeys(self.warnings)),"summary":self.summary,"safety_note":self.safety_note,"success":self.success,"message":self.message,"metadata":self.metadata}
