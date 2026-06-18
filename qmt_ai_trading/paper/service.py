"""Paper trading service layer after Human Approval and Risk Gate."""
from __future__ import annotations
from enum import Enum
from typing import Any
from uuid import uuid4
from datetime import datetime, timezone

from qmt_ai_trading.approval.models import ApprovalCheckResult, ApprovalRequest, ApprovalStatus
from qmt_ai_trading.approval.store import ApprovalStore
from .broker import PaperBroker
from .models import PaperExecutionReport, PaperOrder, PaperOrderStatus, PaperSubmitResult
from .store import PaperOrderStore, json_safe

def _now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def _value(v): return v.value if isinstance(v, Enum) else str(v)
def _allowed(d: Any) -> bool:
    if isinstance(d, dict): return bool(d.get('allowed') is True)
    return bool(getattr(d, 'allowed', False) is True)

def check_approval_for_paper(request: ApprovalRequest) -> ApprovalCheckResult:
    status = _value(request.status)
    allowed = status == ApprovalStatus.APPROVED.value
    msg = 'Approval is APPROVED; paper trading may continue to RiskDecision confirmation.' if allowed else f'Approval status is {status}; paper trading is blocked.'
    return ApprovalCheckResult(request.approval_id, allowed, status, msg, {'paper_only_no_qmt_order': True})

def require_risk_allowed_for_paper(request: ApprovalRequest) -> tuple[bool, str]:
    if not request.risk_decisions:
        return False, 'risk_decisions are missing; paper trading is blocked by default.'
    if not all(_allowed(d) for d in request.risk_decisions):
        return False, 'one or more RiskDecision entries are not allowed; paper trading is blocked.'
    return True, 'RiskDecision allowed=True confirmed for paper trading.'

def paper_orders_from_approval_request(request: ApprovalRequest, broker: PaperBroker, price_map: dict[str,float] | None = None) -> list[PaperOrder]:
    return broker.submit_intents(request.trade_intents, request.approval_id, request.run_id, price_map)

def create_paper_execution_report(approval_id: str, run_id: str, orders: list[PaperOrder]) -> PaperExecutionReport:
    statuses = [_value(o.status) for o in orders]
    report = PaperExecutionReport(report_id=uuid4().hex, approval_id=approval_id, run_id=run_id, created_at=_now(), total_orders=len(orders), submitted_count=sum(s in {'SUBMITTED','FILLED','PARTIALLY_FILLED'} for s in statuses), filled_count=statuses.count('FILLED'), rejected_count=statuses.count('REJECTED'), cancelled_count=statuses.count('CANCELLED'), orders=[json_safe(o) for o in orders], success=bool(orders) and not all(s == 'REJECTED' for s in statuses), message='Paper trading only. No QMT order has been submitted.', metadata={'dry_run': True, 'paper_only_no_qmt_order': True})
    return report

def submit_approved_request_to_paper(approval_id: str, approval_store: ApprovalStore | None = None, paper_store: PaperOrderStore | None = None, broker: PaperBroker | None = None, price_map: dict[str,float] | None = None) -> PaperSubmitResult:
    astore = approval_store or ApprovalStore()
    pstore = paper_store or PaperOrderStore()
    req = astore.load_request(approval_id)
    check = check_approval_for_paper(req)
    if not check.allowed:
        return PaperSubmitResult(False, approval_id, False, [], None, check.message, {'paper_only_no_qmt_order': True})
    if not req.trade_intents:
        return PaperSubmitResult(False, approval_id, False, [], None, 'approval request has no trade_intents; paper trading is blocked.', {'paper_only_no_qmt_order': True})
    risk_ok, risk_msg = require_risk_allowed_for_paper(req)
    if not risk_ok:
        return PaperSubmitResult(False, approval_id, False, [], None, risk_msg, {'paper_only_no_qmt_order': True})
    br = broker or PaperBroker(store=pstore)
    orders = paper_orders_from_approval_request(req, br, price_map)
    report = create_paper_execution_report(req.approval_id, req.run_id, orders)
    pstore.save_report(report)
    return PaperSubmitResult(report.success, approval_id, True, orders, report, report.message, {'risk_message': risk_msg, 'paper_only_no_qmt_order': True})

def cancel_paper_order(paper_order_id: str, paper_store: PaperOrderStore | None = None, reason: str | None = None) -> PaperOrder:
    return PaperBroker(store=paper_store or PaperOrderStore(), auto_fill=False).cancel_order(paper_order_id, reason)

def list_paper_orders(paper_store: PaperOrderStore | None = None, status: str | None = None, approval_id: str | None = None, symbol: str | None = None) -> list[PaperOrder]:
    return (paper_store or PaperOrderStore()).list_orders(status=status, approval_id=approval_id, symbol=symbol)
