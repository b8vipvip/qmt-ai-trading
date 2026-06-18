"""Formatters for Agent Research context and memo."""
from __future__ import annotations
import json
from .models import AgentResearchContext, AgentResearchMemo, to_jsonable

def format_agent_research_context(context: AgentResearchContext) -> str:
    return json.dumps(to_jsonable(context), ensure_ascii=False, indent=2, sort_keys=True)

def format_human_review_checklist(memo: AgentResearchMemo) -> str:
    return "\n".join(f"- [ ] {item}" for item in memo.human_review_checklist) if memo.human_review_checklist else "- [ ] No checklist items generated."

def format_agent_research_memo_markdown(memo: AgentResearchMemo) -> str:
    return "\n".join([
        f"# {memo.title}", f"- Memo ID: {memo.memo_id}", f"- Run ID: {memo.run_id}", f"- Mode: {memo.mode}", f"- Success: {memo.success}", "",
        "## Executive summary", memo.executive_summary or "No executive summary.", "",
        "## Signal explanation", memo.signal_explanation or "No signal explanation.", "",
        "## Risk summary", memo.risk_summary or "No risk summary.", "",
        "## Portfolio summary", memo.portfolio_summary or "No portfolio summary.", "",
        "## Monitoring summary", memo.monitoring_summary or "No monitoring summary.", "",
        "## Backtest summary", memo.backtest_summary or "No backtest summary.", "",
        "## Candidate comparison", memo.candidate_comparison or "No candidate comparison.", "",
        "## Human review checklist", format_human_review_checklist(memo), "",
        "## Safety note", memo.safety_note,
    ])

def format_agent_research_memo_json(memo: AgentResearchMemo) -> str:
    return json.dumps(to_jsonable(memo), ensure_ascii=False, indent=2, sort_keys=True)
