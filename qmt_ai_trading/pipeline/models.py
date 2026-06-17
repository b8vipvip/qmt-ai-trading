"""Data contracts for the daily signal pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from qmt_ai_trading.common.types import RiskDecision, TradeIntent


@dataclass(slots=True)
class PipelineContext:
    """Execution context for one dry-run/shadow pipeline run."""

    run_id: str
    trade_date: date | str
    dry_run: bool = True
    symbols: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PipelineStepResult:
    """Structured status for one pipeline orchestration step."""

    name: str
    success: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PipelineResult:
    """End-to-end output of the daily signal pipeline."""

    context: PipelineContext
    steps: list[PipelineStepResult] = field(default_factory=list)
    research_scores: list[Any] = field(default_factory=list)
    candidates: list[Any] = field(default_factory=list)
    trade_intents: list[TradeIntent] = field(default_factory=list)
    risk_decisions: list[RiskDecision] = field(default_factory=list)
    backtest_result: Any = None
    shadow_replay_result: Any = None
    report_text: str = ""
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
