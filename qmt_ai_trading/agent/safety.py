"""Safety checks for the read-only Agent Research Layer."""
from __future__ import annotations
from dataclasses import replace
from typing import Any
from .models import AgentActionPolicy, AgentResearchContext, AgentResearchMemo, to_jsonable

FORBIDDEN_TRADING_LANGUAGE = ["立即下单", "绕过风控", "直接买入", "无需审批", "提交订单", "实盘执行"]
SENSITIVE_KEYS = ("token", "key", "password", "secret", "account", "credential")

class AgentPolicyError(ValueError):
    pass

def build_default_agent_policy() -> AgentActionPolicy:
    return AgentActionPolicy()

def validate_agent_policy(policy: AgentActionPolicy) -> dict[str, Any]:
    blocked = [name for name in ("allow_order_generation","allow_qmt_access","allow_xttrader","allow_external_network","allow_real_notification","allow_approval_mutation","allow_paper_submission") if getattr(policy, name, False)]
    return {"allowed": not blocked, "blocked": blocked, "message": "read-only policy" if not blocked else "blocked unsafe Agent policy: " + ", ".join(blocked)}

def assert_agent_read_only(policy: AgentActionPolicy) -> None:
    result = validate_agent_policy(policy)
    if not result["allowed"]:
        raise AgentPolicyError(result["message"])

def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            ks = str(k).lower()
            if any(s in ks for s in SENSITIVE_KEYS):
                out[str(k)] = "<redacted>"
            else:
                out[str(k)] = _sanitize(v)
        return out
    if isinstance(value, list): return [_sanitize(v) for v in value]
    if isinstance(value, tuple): return [_sanitize(v) for v in value]
    return value

def sanitize_agent_context(context: AgentResearchContext) -> AgentResearchContext:
    data = _sanitize(to_jsonable(context))
    return AgentResearchContext(**data)

def contains_forbidden_trading_language(text: str) -> bool:
    return any(term in (text or "") for term in FORBIDDEN_TRADING_LANGUAGE)

def validate_agent_memo_safety(memo: AgentResearchMemo) -> dict[str, Any]:
    text = "\n".join([memo.executive_summary, memo.signal_explanation, memo.risk_summary, memo.portfolio_summary, memo.monitoring_summary, memo.backtest_summary, memo.candidate_comparison, "\n".join(memo.human_review_checklist), memo.safety_note])
    forbidden = [term for term in FORBIDDEN_TRADING_LANGUAGE if term in text]
    return {"allowed": not forbidden, "blocked": bool(forbidden), "warnings": forbidden, "message": "safe" if not forbidden else "blocked forbidden trading language: " + ", ".join(forbidden)}
