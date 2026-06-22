from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass(frozen=True)
class XtTraderBoundaryConfig:
    enabled: bool = False
    dry_run: bool = True
    read_only: bool = True
    allow_import_xttrader: bool = False
    allow_create_xtquant_trader: bool = False
    allow_connect_trade_session: bool = False
    allow_account_query: bool = False
    allow_position_query: bool = False
    allow_order_query: bool = False
    allow_trade_query: bool = False
    allow_order_submit: bool = False
    allow_order_cancel: bool = False
    allow_async_order: bool = False
    allow_auto_approve: bool = False
    requires_human_approval: bool = True
    paper_trading_required: bool = True
    risk_gate_required: bool = True
    kill_switch_required: bool = True
    max_single_order_amount: int = 0
    max_daily_order_amount: int = 0
    allowed_symbols: list[str] = field(default_factory=list)
    notes: str = "Stage90 boundary only; xttrader disabled"
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class OrderPreview:
    preview_id: str
    source_paper_order_id: str
    symbol: str
    side: str
    quantity: int
    reference_price: float
    estimated_amount: float
    risk_decision: str
    requires_human_approval: bool = True
    submit_enabled: bool = False
    real_order_submitted: bool = False
    order_submit_blocked: bool = True
    block_reason: str = "xttrader boundary is disabled by safety gate"
    preview_status: str = "READY_FOR_MANUAL_REVIEW"
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
