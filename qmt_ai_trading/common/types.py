"""Shared structured types for the qmt_ai_trading package.

These dataclasses are intentionally dependency-light and are used as the
contract between strategy, agent, risk, and gateway layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(slots=True)
class TradeIntent:
    """Structured trade request generated before risk validation."""

    symbol: str
    side: str
    quantity: int = 0
    target_percent: float = 0.0
    price_type: str = "LATEST"
    reason: str = ""
    source: str = ""
    dry_run: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class RiskDecision:
    """Risk gate decision for a TradeIntent."""

    allowed: bool
    reasons: list[str] = field(default_factory=list)
    adjusted_quantity: Optional[int] = None
    risk_level: str = "LOW"


@dataclass(slots=True)
class AgentDecision:
    """Structured analysis output from an agent."""

    symbol: str
    signal: str
    confidence: float
    score: float
    max_position_pct: float
    reasons: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OrderResult:
    """Gateway order submission result."""

    success: bool
    order_id: Optional[str] = None
    message: str = ""
    raw: Optional[dict] = None
