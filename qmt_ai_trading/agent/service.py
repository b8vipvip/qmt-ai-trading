"""Service layer for read-only Agent Research."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .context import build_agent_context_from_files, build_agent_context_from_pipeline_result
from .formatters import format_agent_research_memo_json, format_agent_research_memo_markdown
from .models import AgentActionPolicy, AgentResearchContext, AgentResearchMemo
from .safety import build_default_agent_policy, sanitize_agent_context, validate_agent_memo_safety, validate_agent_policy
from .summarizer import AgentSummarizerConfig, summarize_with_local_rules, SAFETY_NOTE

def run_agent_research(context: AgentResearchContext, config: AgentSummarizerConfig | None = None, policy: AgentActionPolicy | None = None) -> AgentResearchMemo:
    policy = policy or build_default_agent_policy(); check=validate_agent_policy(policy)
    if not check["allowed"]:
        return AgentResearchMemo(run_id=context.run_id, success=False, message=check["message"], safety_note=SAFETY_NOTE)
    memo = summarize_with_local_rules(sanitize_agent_context(context), config or AgentSummarizerConfig())
    safety = validate_agent_memo_safety(memo)
    if safety["blocked"]:
        memo.success = False; memo.message = safety["message"]; memo.metadata["safety"] = safety
    return memo

def run_agent_research_from_pipeline_result(pipeline_result: Any, config: AgentSummarizerConfig | None = None, policy: AgentActionPolicy | None = None, monitoring_report: Any = None, long_backtest_result: Any = None) -> AgentResearchMemo:
    return run_agent_research(build_agent_context_from_pipeline_result(pipeline_result, monitoring_report=monitoring_report, long_backtest_result=long_backtest_result), config=config, policy=policy)

def run_agent_research_from_files(pipeline_report: str | Path | None = None, monitoring_report: str | Path | None = None, long_backtest_json: str | Path | None = None, portfolio_plan_json: str | Path | None = None, config: AgentSummarizerConfig | None = None, policy: AgentActionPolicy | None = None) -> AgentResearchMemo:
    ctx = build_agent_context_from_files(pipeline_report, monitoring_report, long_backtest_json, portfolio_plan_json)
    return run_agent_research(ctx, config=config, policy=policy)

def save_agent_research_memo(memo: AgentResearchMemo, output_path: str | Path) -> Path:
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
    text = format_agent_research_memo_json(memo) if p.suffix.lower()==".json" else format_agent_research_memo_markdown(memo)
    p.write_text(text, encoding="utf-8"); return p

def load_agent_research_memo(path: str | Path) -> AgentResearchMemo:
    data=json.loads(Path(path).read_text(encoding="utf-8")); return AgentResearchMemo(**data)
