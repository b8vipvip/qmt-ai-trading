"""Human-readable reporting for dry-run/shadow pipeline results."""

from __future__ import annotations

from qmt_ai_trading.pipeline.models import PipelineResult
from qmt_ai_trading.pipeline.data_source import MOCK_FALLBACK_WARNING


def format_pipeline_report(result: PipelineResult) -> str:
    """Format a safe daily dry-run/shadow report without sensitive data."""

    mode = "dry-run / shadow" if result.context.dry_run else "non-dry-run blocked by policy"
    lines = [
        "# QMT AI Trading Daily Signal Report",
        f"- Run ID: {result.context.run_id}",
        f"- Trade Date: {result.context.trade_date}",
        f"- Mode: {mode}",
        f"- Success: {result.success}",
        "",
        "## Steps",
    ]
    ds = result.metadata.get("data_source") or result.context.metadata.get("data_source") or {}
    if ds:
        quality = str(ds.get("quality_level") or "")
        lines.extend(["", "## Data Source", f"- selected_source: {ds.get('selected_source', '')}", f"- cache_root: {(ds.get('metadata') or {}).get('cache_root', '')}", f"- coverage_ratio: {float(ds.get('coverage_ratio', 0.0) or 0.0):.4f}", f"- confidence: {ds.get('confidence', '')}", f"- quality_level: {quality}", f"- selected_cache_type: {ds.get('selected_cache_type', '')}", f"- quality_report_path: {ds.get('quality_report_path') or ''}", f"- quality_report_decision: {ds.get('quality_report_decision') or ''}", f"- fallback_used: {ds.get('fallback_used', False)}", f"- allow_trade_intents: {ds.get('allow_trade_intents', False)}", f"- remediation: {ds.get('remediation', '')}", f"- message: {ds.get('message', '')}"])
        if ds.get("fallback_used") or ds.get("selected_source") == "mock_fallback":
            lines.append(f"- WARNING: {MOCK_FALLBACK_WARNING}")
        if quality in {"UNKNOWN", "LOW", "UNAVAILABLE"} or ds.get("selected_source") in {"cached_unknown_quality", "blocked_missing_quality"}:
            lines.append("- WARNING: Cache quality is not high enough for live trading decisions.")
        if ds.get("selected_source") == "cached_real_data":
            lines.append("- NOTICE: This is still dry-run/shadow output and not an order instruction.")
        lines.append("")
    for step in result.steps:
        status = "OK" if step.success else "FAILED"
        lines.append(f"- {step.name}: {status} - {step.message}")
        for error in step.errors:
            lines.append(f"  - error: {error}")

    lines.extend(["", "## Candidates"])
    if result.candidates:
        for item in result.candidates:
            lines.append(f"- {getattr(item, 'symbol', '')}: score={getattr(item, 'score', 0):.2f}, eligible={getattr(item, 'eligible', True)}, reason={getattr(item, 'reason', '')}")
    else:
        lines.append("- No candidates generated.")

    lines.extend(["", "## TradeIntents"])
    if result.trade_intents:
        for intent in result.trade_intents:
            lines.append(f"- {intent.symbol} {intent.side} qty={intent.quantity} target={intent.target_percent:.4f} dry_run={intent.dry_run} reason={intent.reason}")
    else:
        lines.append(f"- No trade intents generated. Reason: {result.metadata.get('no_intent_reason', 'no eligible candidates or empty input')}")

    plan = result.metadata.get("portfolio_plan")
    if plan is not None:
        from qmt_ai_trading.portfolio.formatters import format_portfolio_plan_markdown
        lines.extend(["", format_portfolio_plan_markdown(plan), ""])

    lines.extend(["", "## RiskDecision"])
    if result.risk_decisions:
        for decision in result.risk_decisions:
            lines.append(f"- allowed={decision.allowed} risk_level={decision.risk_level} adjusted_quantity={decision.adjusted_quantity} reasons={'; '.join(decision.reasons)}")
    else:
        lines.append("- No risk decisions because no trade intents were generated.")

    dq = result.metadata.get("data_quality_tracking") if isinstance(result.metadata, dict) else None
    if dq:
        lines.extend(["", "## Data Quality Tracking", f"- report_id: {dq.get('report_id', '')}", f"- output_path: {dq.get('output_path', '')}", "- summary:"])
        for k, v in (dq.get("summary") or {}).items():
            lines.append(f"  - {k}: {v}")
        lines.append(f"- safety_note: {dq.get('safety_note', '')}")

    agent = result.metadata.get("agent_research") if isinstance(result.metadata, dict) else None
    if agent:
        lines.extend(["", "## Agent Research", f"- memo_id: {agent.get('memo_id', '')}", f"- mode: {agent.get('mode', '')}", f"- success: {agent.get('success', False)}", f"- output_path: {agent.get('output_path', '')}", f"- executive_summary: {agent.get('executive_summary', '')}", f"- risk_summary: {agent.get('risk_summary', '')}", "- human_review_checklist:"])
        for item in agent.get("human_review_checklist", []) or []:
            lines.append(f"  - {item}")
        lines.append(f"- safety_note: {agent.get('safety_note', '')}")

    live_gray = result.metadata.get("live_gray_readiness") if isinstance(result.metadata, dict) else None
    if live_gray:
        lines.extend(["", "## Live Gray Readiness", f"- decision: {live_gray.get('decision', '')}", f"- output_path: {live_gray.get('output_path', '')}", "- summary:"])
        for k, v in (live_gray.get("summary") or {}).items():
            lines.append(f"  - {k}: {v}")
        lines.append("- failed checks:")
        failed = live_gray.get("failed_checks") or []
        if failed:
            for item in failed:
                lines.append(f"  - {item.get('check_id', '')}: {item.get('message', '')}")
        else:
            lines.append("  - None")
        lines.append("- manual review items:")
        for item in live_gray.get("manual_review_items", []) or []:
            lines.append(f"  - {item}")
        lines.append(f"- safety_note: {live_gray.get('safety_note', '')}")

    bt = result.backtest_result
    lines.extend(["", "## Backtest Summary"])
    if bt is None:
        lines.append("- Backtest not available.")
    else:
        lines.append(f"- initial_cash={getattr(bt, 'initial_cash', 0.0):.2f} final_asset={getattr(bt, 'final_asset', 0.0):.2f} total_return={getattr(bt, 'total_return', 0.0):.6f} max_drawdown={getattr(bt, 'max_drawdown', 0.0):.6f} win_rate={getattr(bt, 'win_rate', 0.0):.6f} trade_count={getattr(bt, 'trade_count', 0)}")

    lines.extend(["", "Note: This report is for dry-run/shadow review only and is not an order instruction."])
    return "\n".join(lines)
