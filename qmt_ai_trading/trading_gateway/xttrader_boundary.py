from __future__ import annotations
from typing import Any
from .models import XtTraderBoundaryConfig, OrderPreview

DISABLED_MESSAGE = "xttrader boundary is disabled by safety gate"

def disabled_payload(status: str = "DISABLED") -> dict[str, Any]:
    return {
        "status": status, "enabled": False, "dry_run": True, "read_only": True,
        "xttrader_imported": False, "trade_session_connected": False,
        "account_query_enabled": False, "order_submit_enabled": False,
        "real_order_submitted": False, "requires_human_approval": True,
        "safety_status": "DISABLED_FOR_SAFETY", "message": DISABLED_MESSAGE,
    }

class XtTraderBoundaryAdapter:
    def __init__(self, config: XtTraderBoundaryConfig):
        self.config = config

    def check_config(self) -> dict[str, Any]:
        payload = disabled_payload()
        payload.update({"config": self.config.to_dict(), "blocked_by_safety": True})
        return payload

    def probe_import(self) -> dict[str, Any]:
        return {**disabled_payload(), "probe": "import", "probe_status": "DISABLED", "attempt_status": "NOT_ATTEMPTED", "block_status": "BLOCKED_BY_SAFETY"}

    def probe_connection(self) -> dict[str, Any]:
        return {**disabled_payload(), "probe": "connection", "probe_status": "DISABLED", "attempt_status": "NOT_ATTEMPTED", "block_status": "BLOCKED_BY_SAFETY"}

    def probe_account_query(self) -> dict[str, Any]:
        return {**disabled_payload(), "probe": "account_query", "probe_status": "DISABLED", "attempt_status": "NOT_ATTEMPTED", "block_status": "BLOCKED_BY_SAFETY"}

    def probe_order_submit(self) -> dict[str, Any]:
        return {**disabled_payload(), "probe": "order_submit", "probe_status": "DISABLED", "attempt_status": "NOT_ATTEMPTED", "block_status": "BLOCKED_BY_SAFETY"}

    def build_order_preview(self, paper_order: dict[str, Any], risk_decision: dict[str, Any] | None) -> dict[str, Any]:
        order_id = str(paper_order.get("order_id") or paper_order.get("paper_order_id") or paper_order.get("intent_id") or "paper-order")
        symbol = str(paper_order.get("symbol") or "UNKNOWN")
        side = str(paper_order.get("side") or paper_order.get("signal") or paper_order.get("trade_side") or "hold").lower()
        qty = int(float(paper_order.get("quantity") or 0))
        price = float(paper_order.get("reference_price") or paper_order.get("price") or paper_order.get("intent_price") or 0.0)
        allowed = bool((risk_decision or {}).get("allowed", False)) or str((risk_decision or {}).get("decision", "")).upper() in {"APPROVED_DRY_RUN", "PASS"}
        decision = str((risk_decision or {}).get("decision") or ("APPROVED_DRY_RUN" if allowed else "REJECTED"))
        if side == "hold" or qty <= 0:
            status = "NO_ACTION"
            reason = "hold or zero quantity; no real order action"
        elif not allowed:
            status = "REJECTED_BY_RISK"
            reason = "risk gate did not approve this paper order"
        else:
            status = "READY_FOR_MANUAL_REVIEW"
            reason = DISABLED_MESSAGE
        return OrderPreview(
            preview_id=f"preview-{order_id}", source_paper_order_id=order_id, symbol=symbol, side=side,
            quantity=qty, reference_price=price, estimated_amount=round(qty * price, 4),
            risk_decision=decision, block_reason=reason, preview_status=status,
        ).to_dict()
