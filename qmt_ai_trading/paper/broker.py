"""Pure local paper broker. It never calls QMT or xttrader."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .models import PaperOrder, PaperOrderSide, PaperOrderStatus
from .store import PaperOrderStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _get(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _side(value: Any) -> str:
    raw = value.value if hasattr(value, "value") else value
    return str(raw or "").upper()


class PaperBroker:
    def __init__(self, store: PaperOrderStore | None = None, auto_fill: bool = True, default_fill_price: float = 0.0) -> None:
        self.store = store or PaperOrderStore()
        self.auto_fill = auto_fill
        self.default_fill_price = float(default_fill_price or 0.0)

    def submit_order(self, order: PaperOrder) -> PaperOrder:
        if not order.created_at:
            order.created_at = _now()
        order.dry_run = True
        if _side(order.side) == PaperOrderSide.HOLD.value:
            order.status = PaperOrderStatus.CREATED.value
            order.reason = order.reason or "HOLD intent is recorded only; no paper order is submitted."
            return self.store.save_order(order) and order
        if int(order.quantity or 0) <= 0:
            return self.reject_order(order, "quantity must be positive for paper submission")
        if _side(order.side) == PaperOrderSide.BUY.value and int(order.quantity) % 100 != 0:
            return self.reject_order(order, "A-share BUY quantity must be a multiple of 100 shares")
        order.status = PaperOrderStatus.SUBMITTED.value
        order.submitted_at = _now()
        self.store.save_order(order)
        if self.auto_fill:
            return self.fill_order(order.paper_order_id)
        return order

    def cancel_order(self, paper_order_id: str, reason: str | None = None) -> PaperOrder:
        return self.store.update_order_status(paper_order_id, PaperOrderStatus.CANCELLED, cancelled_at=_now(), reason=reason or "cancelled by local paper broker")

    def reject_order(self, order: PaperOrder, reason: str) -> PaperOrder:
        order.status = PaperOrderStatus.REJECTED.value
        order.rejected_at = _now()
        order.reason = reason
        order.dry_run = True
        self.store.save_order(order)
        return order

    def fill_order(self, paper_order_id: str, price: float | None = None, quantity: int | None = None) -> PaperOrder:
        order = self.store.load_order(paper_order_id)
        fill_price = price if price is not None else (order.requested_price or self.default_fill_price)
        fill_quantity = quantity if quantity is not None else order.quantity
        return self.store.update_order_status(paper_order_id, PaperOrderStatus.FILLED, filled_at=_now(), filled_price=float(fill_price or 0.0), filled_quantity=int(fill_quantity or 0))

    def submit_intents(self, trade_intents: Any, approval_id: str, run_id: str, price_map: dict[str, float] | None = None) -> list[PaperOrder]:
        orders = []
        prices = price_map or {}
        for intent in list(trade_intents or []):
            symbol = str(_get(intent, "symbol", ""))
            price = float(prices.get(symbol, _get(intent, "requested_price", _get(intent, "price", self.default_fill_price)) or 0.0))
            order = PaperOrder(paper_order_id=uuid4().hex, approval_id=approval_id, run_id=run_id, symbol=symbol, side=_get(intent, "side", "HOLD"), quantity=int(_get(intent, "quantity", 0) or 0), target_percent=float(_get(intent, "target_percent", 0.0) or 0.0), requested_price=price, created_at=_now(), source=str(_get(intent, "source", "approval")), metadata={"paper_only_no_qmt_order": True})
            orders.append(self.submit_order(order))
        return orders
