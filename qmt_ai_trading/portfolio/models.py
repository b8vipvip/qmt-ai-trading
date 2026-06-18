"""Portfolio management dataclasses for dry-run/paper planning only."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class PortfolioWeightMethod(str, Enum):
    EQUAL_WEIGHT = "equal_weight"
    SCORE_WEIGHT = "score_weight"
    RISK_ADJUSTED_WEIGHT = "risk_adjusted_weight"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def round_lot(quantity: int, lot: int = 100) -> int:
    return max(0, (int(quantity or 0) // int(lot or 100)) * int(lot or 100))

@dataclass
class PortfolioPosition:
    symbol: str
    quantity: int = 0
    market_value: float = 0.0
    weight: float = 0.0
    cost_basis: float = 0.0
    last_price: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self): self.quantity = round_lot(self.quantity)

@dataclass
class PortfolioSnapshot:
    snapshot_id: str
    created_at: str = field(default_factory=_now)
    cash: float = 0.0
    total_asset: float = 0.0
    positions: list[PortfolioPosition] = field(default_factory=list)
    source: str = "local_mock_snapshot"
    dry_run: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PortfolioTarget:
    symbol: str
    target_weight: float = 0.0
    target_value: float = 0.0
    score: float = 0.0
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class PortfolioAdjustment:
    symbol: str
    current_weight: float = 0.0
    target_weight: float = 0.0
    delta_weight: float = 0.0
    current_value: float = 0.0
    target_value: float = 0.0
    side: str = "HOLD"
    quantity: int = 0
    estimated_price: float = 0.0
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self): self.quantity = round_lot(self.quantity)

@dataclass
class PortfolioPlan:
    plan_id: str
    created_at: str = field(default_factory=_now)
    run_id: str = ""
    method: str = PortfolioWeightMethod.SCORE_WEIGHT.value
    cash_reserve_ratio: float = 0.2
    max_symbol_weight: float = 0.3
    max_portfolio_weight: float = 0.8
    rebalance_threshold: float = 0.05
    total_asset: float = 0.0
    investable_asset: float = 0.0
    targets: list[PortfolioTarget] = field(default_factory=list)
    adjustments: list[PortfolioAdjustment] = field(default_factory=list)
    trade_intents: list[Any] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    success: bool = True
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum): return value.value
    if is_dataclass(value): return {k: to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, list): return [to_jsonable(v) for v in value]
    if isinstance(value, dict): return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, datetime): return value.isoformat()
    return value
