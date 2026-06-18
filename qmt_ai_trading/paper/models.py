"""Local paper trading models for Stage 22 dry-run execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PaperOrderStatus(str, Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class PaperOrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class PaperOrder:
    paper_order_id: str
    approval_id: str
    run_id: str
    symbol: str
    side: PaperOrderSide | str
    quantity: int = 0
    target_percent: float = 0.0
    requested_price: float = 0.0
    filled_price: float = 0.0
    filled_quantity: int = 0
    status: PaperOrderStatus | str = PaperOrderStatus.CREATED
    created_at: str = ""
    submitted_at: str | None = None
    filled_at: str | None = None
    cancelled_at: str | None = None
    rejected_at: str | None = None
    reason: str = ""
    source: str = "paper"
    dry_run: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaperExecutionReport:
    report_id: str
    approval_id: str
    run_id: str
    created_at: str
    total_orders: int = 0
    submitted_count: int = 0
    filled_count: int = 0
    rejected_count: int = 0
    cancelled_count: int = 0
    orders: list[dict[str, Any]] = field(default_factory=list)
    success: bool = False
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PaperSubmitResult:
    success: bool
    approval_id: str
    allowed: bool
    orders: list[PaperOrder] = field(default_factory=list)
    report: PaperExecutionReport | None = None
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
