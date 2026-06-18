"""CLI-friendly formatters for approval objects."""

from __future__ import annotations

from .models import ApprovalCheckResult, ApprovalDecision, ApprovalRequest

NO_ORDER = "Approval is not an order. No QMT order has been submitted."
PENDING_BLOCK = "Pending approval; execution is blocked."


def _status(value: object) -> str:
    return getattr(value, "value", str(value))


def format_approval_request(request: ApprovalRequest) -> str:
    lines = [
        NO_ORDER,
        f"Approval ID: {request.approval_id}",
        f"Run ID: {request.run_id}",
        f"Status: {_status(request.status)}",
        f"Created at: {request.created_at}",
        f"Expires at: {request.expires_at}",
        f"TradeIntent count: {len(request.trade_intents)}",
        f"RiskDecision count: {len(request.risk_decisions)}",
        f"Confidence: {request.confidence}",
        f"Summary: {request.summary}",
    ]
    if _status(request.status) == "PENDING":
        lines.append(PENDING_BLOCK)
    return "\n".join(lines)


def format_approval_decision(decision: ApprovalDecision) -> str:
    return "\n".join([NO_ORDER, f"Approval ID: {decision.approval_id}", f"Action: {_status(decision.action)}", f"Status after: {_status(decision.status_after)}", f"Decided by: {decision.decided_by}", f"Comment: {decision.comment}"])


def format_approval_check_result(result: ApprovalCheckResult) -> str:
    lines = [NO_ORDER, f"Approval ID: {result.approval_id}", f"Allowed: {result.allowed}", f"Status: {_status(result.status)}", f"Message: {result.message}"]
    if _status(result.status) == "PENDING":
        lines.append(PENDING_BLOCK)
    return "\n".join(lines)


def format_approval_list(requests: list[ApprovalRequest]) -> str:
    lines = [NO_ORDER, f"Approval requests: {len(requests)}"]
    for req in requests:
        lines.append(f"- {req.approval_id} status={_status(req.status)} run_id={req.run_id} intents={len(req.trade_intents)} expires_at={req.expires_at}")
    if any(_status(req.status) == "PENDING" for req in requests):
        lines.append(PENDING_BLOCK)
    return "\n".join(lines)
