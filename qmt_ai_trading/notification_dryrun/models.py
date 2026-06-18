from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

SAFETY_NOTE = "Notification dry-run does not send real messages, does not call external networks, and does not read real tokens."

def _now(): return datetime.now(timezone.utc).isoformat()
def _id(prefix): return f"{prefix}-{uuid4().hex[:12]}"
def _jsonify(v):
    if isinstance(v, Enum): return v.value
    if hasattr(v, 'to_dict'): return v.to_dict()
    if isinstance(v, list): return [_jsonify(x) for x in v]
    if isinstance(v, dict): return {str(k): _jsonify(x) for k,x in v.items()}
    return v

class NotificationChannel(str, Enum):
    CONSOLE="CONSOLE"; FILE="FILE"; EMAIL="EMAIL"; TELEGRAM="TELEGRAM"; WECHAT="WECHAT"
class NotificationSeverity(str, Enum):
    INFO="INFO"; WARNING="WARNING"; ERROR="ERROR"; CRITICAL="CRITICAL"
class NotificationSendMode(str, Enum):
    DRY_RUN="DRY_RUN"; SUPPRESSED="SUPPRESSED"; DISABLED="DISABLED"

@dataclass
class NotificationMessage:
    message_id: str = field(default_factory=lambda: _id('msg'))
    created_at: str = field(default_factory=_now)
    channel: NotificationChannel | str = NotificationChannel.FILE
    severity: NotificationSeverity | str = NotificationSeverity.INFO
    subject: str = ""
    body: str = ""
    source: str = "generic"
    run_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return _jsonify(asdict(self))

@dataclass
class NotificationRecipient:
    recipient_id: str = field(default_factory=lambda: _id('rcpt'))
    channel: NotificationChannel | str = NotificationChannel.FILE
    display_name: str = "dry-run-recipient"
    destination_masked: str = "local-preview"
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return _jsonify(asdict(self))

@dataclass
class NotificationDeliveryPlan:
    plan_id: str = field(default_factory=lambda: _id('plan'))
    created_at: str = field(default_factory=_now)
    send_mode: NotificationSendMode | str = NotificationSendMode.DRY_RUN
    channel: NotificationChannel | str = NotificationChannel.FILE
    recipient: NotificationRecipient = field(default_factory=NotificationRecipient)
    message: NotificationMessage = field(default_factory=NotificationMessage)
    dry_run: bool = True
    real_send_enabled: bool = False
    external_network_enabled: bool = False
    blocked_reasons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return _jsonify(asdict(self))

@dataclass
class NotificationAuditResult:
    audit_id: str = field(default_factory=lambda: _id('audit'))
    created_at: str = field(default_factory=_now)
    passed: bool = True
    severity: NotificationSeverity | str = NotificationSeverity.INFO
    checks: list[dict[str, Any]] = field(default_factory=list)
    blocked_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    safety_note: str = SAFETY_NOTE
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return _jsonify(asdict(self))

@dataclass
class NotificationDryRunReport:
    report_id: str = field(default_factory=lambda: _id('ndr'))
    created_at: str = field(default_factory=_now)
    messages: list[NotificationMessage] = field(default_factory=list)
    recipients: list[NotificationRecipient] = field(default_factory=list)
    delivery_plans: list[NotificationDeliveryPlan] = field(default_factory=list)
    audit_result: NotificationAuditResult = field(default_factory=NotificationAuditResult)
    output_files: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    message: str = "notification dry-run report generated"
    safety_note: str = SAFETY_NOTE
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return _jsonify(asdict(self))
