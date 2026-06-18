"""Context builders for read-only Agent Research."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from uuid import uuid4
from .models import AgentResearchContext, to_jsonable
from .safety import sanitize_agent_context

SENSITIVE_FILENAMES = {".env", ".env.local", "config.json"}

def _safe_obj(obj: Any) -> Any:
    return to_jsonable(obj)

def _read_file(path: str | Path, warnings: list[str]) -> Any:
    p = Path(path)
    if p.name in SENSITIVE_FILENAMES or any(part.lower().startswith(".env") for part in p.parts):
        warnings.append(f"skipped sensitive file: {p}"); return None
    if not p.exists():
        warnings.append(f"missing file: {p}"); return None
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        try: return json.loads(text)
        except Exception as exc: warnings.append(f"json parse failed for {p}: {exc}")
    return {"path": str(p), "text_preview": text[:4000]}

def summarize_data_source(data: Any) -> dict[str, Any]:
    d = _safe_obj(data) or {}
    return d if isinstance(d, dict) else {"value": d}

def summarize_cache_quality(data: Any) -> dict[str, Any]:
    d = summarize_data_source(data)
    return {k: d.get(k) for k in ("quality_level","selected_cache_type","coverage_ratio","quality_report_decision","fallback_used","message") if k in d}

def summarize_candidates(items: Any) -> list[dict[str, Any]]:
    out=[]
    for item in list(items or []):
        d=_safe_obj(item); d=d if isinstance(d,dict) else {"value":d}
        out.append({k:d.get(k) for k in ("symbol","score","eligible","reason","target_percent") if k in d})
    return out

def summarize_trade_intents(items: Any) -> list[dict[str, Any]]:
    out=[]
    for item in list(items or []):
        d=_safe_obj(item); d=d if isinstance(d,dict) else {"value":d}
        out.append({k:d.get(k) for k in ("symbol","side","quantity","target_percent","dry_run","reason") if k in d})
    return out

def summarize_risk_decisions(items: Any) -> list[dict[str, Any]]:
    out=[]
    for item in list(items or []):
        d=_safe_obj(item); d=d if isinstance(d,dict) else {"value":d}
        out.append({k:d.get(k) for k in ("allowed","risk_level","adjusted_quantity","reasons") if k in d})
    return out

def summarize_portfolio_plan(plan: Any) -> dict[str, Any]:
    d=_safe_obj(plan) or {}
    if not isinstance(d,dict): return {}
    return {"target_count": len(d.get("targets") or []), "adjustment_count": len(d.get("adjustments") or []), "trade_intent_count": len(d.get("trade_intents") or []), "warnings": d.get("warnings") or [], "metadata": d.get("metadata") or {}}

def summarize_monitoring_report(report: Any) -> dict[str, Any]:
    d=_safe_obj(report) or {}
    if not isinstance(d,dict): return {}
    return {"success": d.get("success"), "decision": d.get("decision") or d.get("circuit_breaker_decision"), "event_count": len(d.get("events") or []), "alerts": len(d.get("alerts") or []), "summary": d.get("summary") or d.get("message") or ""}

def summarize_long_backtest_result(result: Any) -> dict[str, Any]:
    d=_safe_obj(result) or {}
    if not isinstance(d,dict): return {}
    summary=d.get("summary") if isinstance(d.get("summary"),dict) else d
    return {k: summary.get(k) for k in ("total_return","annualized_return","max_drawdown","volatility","sharpe","win_rate","trade_count") if k in summary}

def build_agent_context_from_pipeline_result(pipeline_result: Any, monitoring_report: Any = None, long_backtest_result: Any = None, warnings: list[str] | None = None) -> AgentResearchContext:
    md = getattr(pipeline_result, "metadata", {}) or {}
    ctx = AgentResearchContext(
        context_id=f"agent-context-{uuid4().hex[:8]}",
        run_id=str(getattr(getattr(pipeline_result, "context", None), "run_id", "")),
        data_source_summary=summarize_data_source(md.get("data_source") or getattr(getattr(pipeline_result,"context",None),"metadata",{}).get("data_source",{})),
        cache_quality_summary=summarize_cache_quality(md.get("data_source") or {}),
        candidates=summarize_candidates(getattr(pipeline_result, "candidates", [])),
        trade_intents=summarize_trade_intents(getattr(pipeline_result, "trade_intents", [])),
        risk_decisions=summarize_risk_decisions(getattr(pipeline_result, "risk_decisions", [])),
        portfolio_plan_summary=summarize_portfolio_plan(md.get("portfolio_plan")),
        monitoring_summary=summarize_monitoring_report(monitoring_report or md.get("monitoring_report")),
        backtest_summary=summarize_long_backtest_result(getattr(pipeline_result, "backtest_result", None)),
        long_backtest_summary=summarize_long_backtest_result(long_backtest_result),
        warnings=list(warnings or []),
        metadata={"source": "pipeline_result"},
    )
    return sanitize_agent_context(ctx)

def build_agent_context_from_files(pipeline_report: str | Path | None = None, monitoring_report: str | Path | None = None, long_backtest_json: str | Path | None = None, portfolio_plan_json: str | Path | None = None) -> AgentResearchContext:
    warnings=[]; pr=_read_file(pipeline_report,warnings) if pipeline_report else None; mr=_read_file(monitoring_report,warnings) if monitoring_report else None; lb=_read_file(long_backtest_json,warnings) if long_backtest_json else None; pp=_read_file(portfolio_plan_json,warnings) if portfolio_plan_json else None
    if not any([pr,mr,lb,pp]): warnings.append("no input files provided; generated empty Agent Research context")
    ctx=AgentResearchContext(context_id=f"agent-context-{uuid4().hex[:8]}", run_id="file-input", data_source_summary=summarize_data_source(pr), cache_quality_summary=summarize_cache_quality(pr if isinstance(pr,dict) else {}), portfolio_plan_summary=summarize_portfolio_plan(pp), monitoring_summary=summarize_monitoring_report(mr), long_backtest_summary=summarize_long_backtest_result(lb), warnings=warnings, metadata={"source":"files"})
    return sanitize_agent_context(ctx)
