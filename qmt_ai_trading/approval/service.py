"""Human approval service helpers.

This module only creates and checks local approval records. It never calls QMT,
xttrader, account queries, order APIs, or notification transports.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from .models import ApprovalAction, ApprovalCheckResult, ApprovalDecision, ApprovalRequest, ApprovalStatus
from .store import ApprovalStore, _json_safe


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _items_to_json(items: Any) -> list[dict[str, Any]]:
    output = []
    for item in list(items or []):
        safe = _json_safe(item)
        output.append(safe if isinstance(safe, dict) else {"value": safe})
    return output


def create_approval_request(
    *,
    run_id: str,
    trade_intents: Any,
    risk_decisions: Any = None,
    data_source: dict[str, Any] | None = None,
    confidence: str | None = None,
    summary: str = "",
    reason: str = "",
    requested_by: str = "pipeline",
    metadata: dict[str, Any] | None = None,
    store: ApprovalStore | None = None,
    expires_hours: float = 24,
    approval_id: str | None = None,
) -> ApprovalRequest:
    created = _utc_now()
    request = ApprovalRequest(
        approval_id=approval_id or uuid4().hex,
        run_id=run_id,
        created_at=_iso(created),
        expires_at=_iso(created + timedelta(hours=expires_hours)),
        status=ApprovalStatus.PENDING,
        trade_intents=_items_to_json(trade_intents),
        risk_decisions=_items_to_json(risk_decisions),
        data_source=_json_safe(data_source or {}),
        confidence=confidence,
        summary=summary,
        reason=reason,
        requested_by=requested_by,
        metadata={"safety": "approval_only_no_order", **dict(metadata or {})},
    )
    if store is not None:
        store.save_request(request)
    return request


def _decide(store: ApprovalStore, approval_id: str, action: ApprovalAction, status: ApprovalStatus, decided_by: str, comment: str = "", metadata: dict[str, Any] | None = None) -> ApprovalDecision:
    decision = ApprovalDecision(approval_id=approval_id, action=action, decided_at=_iso(_utc_now()), decided_by=decided_by, comment=comment, status_after=status, metadata={"no_order_submitted": True, **dict(metadata or {})})
    store.update_status(approval_id, status, decision)
    return decision


def approve_request(store: ApprovalStore, approval_id: str, *, decided_by: str, comment: str = "", metadata: dict[str, Any] | None = None) -> ApprovalDecision:
    return _decide(store, approval_id, ApprovalAction.APPROVE, ApprovalStatus.APPROVED, decided_by, comment, metadata)


def reject_request(store: ApprovalStore, approval_id: str, *, decided_by: str, comment: str = "", metadata: dict[str, Any] | None = None) -> ApprovalDecision:
    return _decide(store, approval_id, ApprovalAction.REJECT, ApprovalStatus.REJECTED, decided_by, comment, metadata)


def cancel_request(store: ApprovalStore, approval_id: str, *, decided_by: str, comment: str = "", metadata: dict[str, Any] | None = None) -> ApprovalDecision:
    return _decide(store, approval_id, ApprovalAction.CANCEL, ApprovalStatus.CANCELLED, decided_by, comment, metadata)


def check_approval(store: ApprovalStore, approval_id: str) -> ApprovalCheckResult:
    store.mark_expired()
    req = store.load_request(approval_id)
    status = req.status.value if isinstance(req.status, Enum) else str(req.status)
    allowed = status == ApprovalStatus.APPROVED.value
    message = "Approval is approved; paper/live execution may continue to the next safety layer." if allowed else f"Approval status is {status}; execution is blocked."
    return ApprovalCheckResult(approval_id=approval_id, allowed=allowed, status=status, message=message, metadata={"no_order_submitted": True})


def require_approval_for_intents(store: ApprovalStore, approval_id: str) -> ApprovalCheckResult:
    result = check_approval(store, approval_id)
    if not result.allowed:
        raise PermissionError(result.message)
    return result


def approval_request_from_pipeline_result(result: Any, *, store: ApprovalStore | None = None, expires_hours: float = 24, requested_by: str = "pipeline") -> ApprovalRequest | None:
    trade_intents = getattr(result, "trade_intents", []) or []
    if not trade_intents:
        return None
    context = getattr(result, "context", None)
    metadata = getattr(result, "metadata", {}) or {}
    data_source = metadata.get("data_source") or getattr(context, "metadata", {}).get("data_source", {}) if context else metadata.get("data_source", {})
    confidence = data_source.get("confidence") if isinstance(data_source, dict) else None
    return create_approval_request(
        run_id=getattr(context, "run_id", "unknown-run"),
        trade_intents=trade_intents,
        risk_decisions=getattr(result, "risk_decisions", []),
        data_source=data_source if isinstance(data_source, dict) else {},
        confidence=confidence,
        summary=f"Pending human approval for {len(trade_intents)} TradeIntent(s).",
        reason="Created after TradeIntent and Risk Gate for human review before paper/live execution.",
        requested_by=requested_by,
        metadata={"pipeline_success": getattr(result, "success", None)},
        store=store,
        expires_hours=expires_hours,
    )
