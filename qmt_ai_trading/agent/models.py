"""Dataclasses for the read-only Agent Research Layer."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class AgentResearchMode(str, Enum):
    MOCK = "mock"
    LOCAL_RULES = "local_rules"
    EXTERNAL_LLM_DISABLED = "external_llm_disabled"

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum): return value.value
    if is_dataclass(value): return {k: to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict): return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)): return [to_jsonable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None: return value
    return str(value)

@dataclass
class AgentResearchSection:
    section_id: str
    title: str
    content: str = ""
    severity: str = "INFO"
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentResearchContext:
    context_id: str = "agent-context"
    created_at: str = field(default_factory=utc_now)
    run_id: str = ""
    data_source_summary: dict[str, Any] = field(default_factory=dict)
    cache_quality_summary: dict[str, Any] = field(default_factory=dict)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    trade_intents: list[dict[str, Any]] = field(default_factory=list)
    risk_decisions: list[dict[str, Any]] = field(default_factory=list)
    portfolio_plan_summary: dict[str, Any] = field(default_factory=dict)
    monitoring_summary: dict[str, Any] = field(default_factory=dict)
    backtest_summary: dict[str, Any] = field(default_factory=dict)
    long_backtest_summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentResearchMemo:
    memo_id: str = "agent-memo"
    created_at: str = field(default_factory=utc_now)
    run_id: str = ""
    mode: str = AgentResearchMode.LOCAL_RULES.value
    title: str = "Agent Research Memo"
    executive_summary: str = ""
    signal_explanation: str = ""
    risk_summary: str = ""
    portfolio_summary: str = ""
    monitoring_summary: str = ""
    backtest_summary: str = ""
    candidate_comparison: str = ""
    human_review_checklist: list[str] = field(default_factory=list)
    safety_note: str = "Agent Research is read-only. It is not an order instruction, does not submit orders, and cannot bypass Risk Gate or Human Approval."
    sections: list[AgentResearchSection] = field(default_factory=list)
    success: bool = True
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentActionPolicy:
    allow_order_generation: bool = False
    allow_qmt_access: bool = False
    allow_xttrader: bool = False
    allow_external_network: bool = False
    allow_real_notification: bool = False
    allow_approval_mutation: bool = False
    allow_paper_submission: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
