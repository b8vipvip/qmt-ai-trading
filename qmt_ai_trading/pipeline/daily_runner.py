"""Daily signal pipeline orchestration for dry-run/shadow review."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from uuid import uuid4

from qmt_ai_trading.backtest.shadow_replay import replay_trade_intents
from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.datahub.symbols import normalize_symbol
from qmt_ai_trading.pipeline.models import PipelineContext, PipelineResult, PipelineStepResult
from qmt_ai_trading.pipeline.data_source import CONFIDENCE_ORDER, build_data_source_policy, choose_pipeline_data_source
from qmt_ai_trading.risk.trade_validator import validate_trade_intent
from qmt_ai_trading.strategies.etf_rotation import build_candidates_from_universe, generate_etf_rotation_intents


def build_pipeline_context(
    trade_date: date | str | None = None,
    *,
    dry_run: bool = True,
    symbols: Iterable[str] | None = None,
    run_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> PipelineContext:
    """Create a safe default pipeline context; dry-run is the default."""

    resolved_date = trade_date or date.today()
    clean_symbols = [normalize_symbol(str(item)) for item in (symbols or []) if str(item).strip()]
    return PipelineContext(
        run_id=run_id or f"daily-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}",
        trade_date=resolved_date,
        dry_run=bool(dry_run),
        symbols=clean_symbols,
        metadata=dict(metadata or {}),
    )


def _record_step(steps: list[PipelineStepResult], name: str, success: bool, message: str, data: Mapping[str, Any] | None = None, errors: Iterable[str] | None = None) -> None:
    steps.append(PipelineStepResult(name=name, success=success, message=message, data=dict(data or {}), errors=[str(item) for item in (errors or [])]))


def run_daily_signal_pipeline(
    *,
    context: PipelineContext | None = None,
    candidates: Iterable[Any] | None = None,
    prices: Mapping[str, float] | None = None,
    top_n: int = 1,
    min_score: float | None = None,
    capital: float | None = None,
    initial_cash: float = 1_000_000.0,
    use_cached_research: bool = False,
    cache_root: str = "market_data",
    research_start_date: str | None = None,
    research_end_date: str | None = None,
    research_frequency: str = "1d",
    min_bars: int = 20,
    allow_partial_research: bool = True,
    cached_strategy_top_n: int = 1,
    cached_strategy_min_score: float | None = None,
    cached_strategy_min_bars: int = 20,
    data_source_mode: str = "cached_real_first",
    quality_report_dir: str = "qmt_data_quality_reports",
    require_quality_report: bool = False,
    allow_unknown_quality_for_dry_run: bool = True,
    allow_mock_cache: bool = False,
    min_quality_level: str = "UNKNOWN",
    allow_mock_fallback: bool = False,
    min_coverage_ratio: float = 0.8,
    min_loaded_symbols: int = 1,
    require_cached_research: bool = False,
    data_source_confidence_required: str | None = None,
    enable_portfolio_plan: bool = False,
    portfolio_method: str = "score_weight",
    portfolio_top_n: int = 2,
    portfolio_cash_reserve_ratio: float = 0.2,
    portfolio_max_symbol_weight: float = 0.3,
    portfolio_max_weight: float = 0.8,
    portfolio_rebalance_threshold: float = 0.05,
    portfolio_total_asset: float = 1_000_000.0,
    portfolio_current_cash: float = 1_000_000.0,
    portfolio_snapshot_path: str | None = None,
    enable_agent_research: bool = False,
    agent_research_output_dir: str = "agent_reports",
    agent_research_mode: str = "local_rules",
    agent_include_monitoring: bool = True,
    agent_include_backtest: bool = True,
    agent_include_human_checklist: bool = True,
    enable_live_gray_readiness: bool = False,
    live_gray_output_dir: str = "live_gray_reports",
    live_gray_allowed_symbols: Iterable[str] | None = None,
    live_gray_max_total_capital: float = 5000.0,
    live_gray_max_single_order_value: float = 1000.0,
    live_gray_max_symbol_weight: float = 0.1,
    live_gray_max_portfolio_weight: float = 0.2,
    live_gray_enabled: bool = False,
    live_enabled: bool = False,
    live_gray_operator_name: str = "",
    enable_data_quality_tracking: bool = False,
    data_quality_tracking_output_dir: str = "data_quality_tracking",
    data_quality_tracking_report_dir: str = "qmt_data_quality_reports",
    data_quality_tracking_cache_root: str | None = None,
    data_quality_tracking_symbols: Iterable[str] | None = None,
    data_quality_tracking_start: str | None = None,
    data_quality_tracking_end: str | None = None,
    enable_notification_dry_run: bool = False,
    notification_dry_run_output_dir: str = "notification_dryrun",
    notification_dry_run_channels: Iterable[str] | str | None = None,
    notification_dry_run_recipients: Iterable[str] | str | None = None,
    notification_dry_run_preview_output_dir: str | None = None,
    enable_gray_rehearsal: bool = False,
    gray_rehearsal_output_dir: str = "gray_rehearsal",
    gray_rehearsal_allowed_symbols: Iterable[str] | None = None,
    gray_rehearsal_max_total_capital: float = 5000.0,
    gray_rehearsal_max_single_order_value: float = 1000.0,
    enable_gray_decision_package: bool = False,
    gray_decision_output_dir: str = "gray_decision",
    gray_decision_allowed_symbols: Iterable[str] | None = None,
    gray_decision_max_total_capital: float = 5000.0,
    gray_decision_max_single_order_value: float = 1000.0,
    gray_decision_max_symbol_weight: float = 0.1,
    gray_decision_max_portfolio_weight: float = 0.2,
    gray_decision_operator_name: str = "",
    gray_decision_reviewer_name: str = "",
    enable_live_manual_prep: bool = False,
    live_manual_prep_output_dir: str = "live_manual_prep",
    live_manual_prep_allowed_symbols: Iterable[str] | None = None,
    live_manual_prep_max_total_capital: float = 5000.0,
    live_manual_prep_max_single_order_value: float = 1000.0,
    live_manual_prep_max_symbol_weight: float = 0.1,
    live_manual_prep_max_portfolio_weight: float = 0.2,
    live_manual_prep_operator_name: str = "",
    live_manual_prep_reviewer_name: str = "",
    live_manual_prep_risk_owner_name: str = "",
    enable_live_env_check: bool = False,
    live_env_check_output_dir: str = "live_env_check",
    live_env_check_allowed_symbols: Iterable[str] | None = None,
    live_env_check_max_total_capital: float = 5000.0,
    live_env_check_max_single_order_value: float = 1000.0,
    live_env_check_max_symbol_weight: float = 0.1,
    live_env_check_max_portfolio_weight: float = 0.2,
    live_env_check_operator_name: str = "",
    live_env_check_reviewer_name: str = "",
) -> PipelineResult:
    """Run the generic daily signal pipeline without connecting to real QMT trading."""

    ctx = context or build_pipeline_context(dry_run=True)
    if not ctx.dry_run:
        ctx.dry_run = True
        ctx.metadata["dry_run_forced"] = True
    steps: list[PipelineStepResult] = []
    result = PipelineResult(context=ctx, steps=steps)

    if data_source_mode == "legacy" and use_cached_research:
        data_source_mode = "cached"
    if candidates is not None and data_source_mode == "cached_real_first":
        data_source_mode = "legacy"
    data_source_policy = build_data_source_policy(mode=data_source_mode, allow_mock_fallback=allow_mock_fallback, min_coverage_ratio=min_coverage_ratio, min_loaded_symbols=min_loaded_symbols, require_cached_research=require_cached_research, quality_report_dir=quality_report_dir, require_quality_report=require_quality_report, allow_unknown_quality_for_dry_run=allow_unknown_quality_for_dry_run, allow_mock_cache=allow_mock_cache, min_quality_level=min_quality_level, cache_root=cache_root, start_date=research_start_date, end_date=research_end_date or str(ctx.trade_date), frequency=research_frequency, min_bars=min_bars)
    decision = choose_pipeline_data_source(data_source_policy, ctx.symbols)
    ctx.metadata["data_source"] = decision.__dict__.copy()
    result.metadata["data_source"] = decision.__dict__.copy()
    _record_step(steps, "data_source_decision", True, decision.message, decision.__dict__)
    _record_step(steps, "data_source_coverage", True, f"coverage={decision.coverage_ratio:.2%} loaded={decision.loaded_symbols}/{decision.total_symbols}", decision.__dict__)
    if data_source_mode == "cached_real_first":
        _record_step(steps, "cache_quality_gate", True, decision.message, decision.__dict__)
    required = data_source_confidence_required.upper() if data_source_confidence_required else None
    if required and CONFIDENCE_ORDER.get(decision.confidence, 0) < CONFIDENCE_ORDER.get(required, 0):
        decision.allow_trade_intents = False
        decision.message = f"data source confidence {decision.confidence} below required {required}"
        ctx.metadata["data_source"] = decision.__dict__.copy()
        result.metadata["data_source"] = decision.__dict__.copy()
        result.metadata["no_intent_reason"] = decision.message

    if decision.selected_source == "mock_fallback":
        ctx.metadata["mock_fallback_warning"] = True
    if data_source_mode == "cached" and decision.selected_source != "cached_research" and candidates is None:
        candidates = []
        ctx.metadata["cached_research"] = {"enabled": True, "success": False, "message": decision.message, "cache_root": str(cache_root)}
        _record_step(steps, "cached_research_load", True, f"warning: {decision.message}", dict(ctx.metadata["cached_research"]))
        _record_step(steps, "cached_research", True, f"warning: {decision.message}", dict(ctx.metadata["cached_research"]))
    if decision.selected_source in {"cached_research", "cached_real_data", "cached_unknown_quality"} and candidates is None:
        try:
            from qmt_ai_trading.research.cache_scoring import score_etf_universe_from_cache
            from qmt_ai_trading.strategies.cached_etf_rotation import CachedETFSignalConfig, generate_cached_etf_rotation_signal

            end_date = research_end_date or str(ctx.trade_date)
            start_date = research_start_date or (date.fromisoformat(str(end_date)) - timedelta(days=max(30, min_bars * 2))).isoformat()
            symbols = ctx.symbols or [item.symbol for item in get_default_etf_universe()]
            scores, dataset = score_etf_universe_from_cache(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                frequency=research_frequency,
                cache_root=cache_root,
                min_bars=min_bars,
                allow_partial=allow_partial_research,
            )
            ctx.metadata["cached_research"] = {
                "enabled": True,
                "success": dataset.success,
                "message": dataset.message,
                "loaded_symbols": dataset.loaded_symbols,
                "failed_symbols": dataset.failed_symbols,
                "cache_root": str(cache_root),
            }
            _record_step(steps, "cached_research_load", True, dataset.message if dataset.success else f"warning: {dataset.message}", dict(ctx.metadata["cached_research"]))
            _record_step(steps, "cached_research", True, dataset.message if dataset.success else f"warning: {dataset.message}", dict(ctx.metadata["cached_research"]))
            _record_step(steps, "cached_research_score", True, f"scored {len(scores)} cached research symbols", {"count": len(scores)})
            signal = generate_cached_etf_rotation_signal(
                scores,
                CachedETFSignalConfig(top_n=cached_strategy_top_n, min_score=cached_strategy_min_score if cached_strategy_min_score is not None else min_score, min_bars=cached_strategy_min_bars),
                capital=capital or initial_cash,
            )
            candidates = signal.candidates
            result.trade_intents = signal.trade_intents
            result.metadata["cached_etf_rotation"] = {"message": signal.message, "selected": len(signal.selected_candidates), "skipped": signal.skipped_symbols}
            if not result.trade_intents:
                result.metadata["no_intent_reason"] = signal.message
            _record_step(steps, "cached_etf_rotation", True, signal.message, dict(result.metadata["cached_etf_rotation"]))
        except Exception as exc:
            candidates = []
            ctx.metadata["cached_research"] = {"enabled": True, "success": False, "message": repr(exc), "cache_root": str(cache_root)}
            _record_step(steps, "cached_research_load", True, "warning: cached research failed; continuing with empty candidates", dict(ctx.metadata["cached_research"]))
            _record_step(steps, "cached_research", True, "warning: cached research failed; continuing with empty candidates", dict(ctx.metadata["cached_research"]))

    try:
        result.candidates = list(candidates or [])
        _record_step(steps, "load_candidates", True, f"loaded {len(result.candidates)} candidates", {"count": len(result.candidates)})
    except Exception as exc:  # orchestration boundary: record and continue empty
        result.candidates = []
        _record_step(steps, "load_candidates", False, "candidate loading failed; continuing with empty input", errors=[repr(exc)])

    try:
        if not decision.allow_trade_intents:
            result.trade_intents = []
            result.metadata["no_intent_reason"] = decision.message or "data source decision disallowed TradeIntent generation"
        elif result.trade_intents:
            pass
        else:
            result.trade_intents = generate_etf_rotation_intents(result.candidates, top_n=top_n, min_score=min_score, dry_run=True, capital=capital or initial_cash)
        if not result.trade_intents and "no_intent_reason" not in result.metadata:
            result.metadata["no_intent_reason"] = "no eligible candidates after strategy selection"
        _record_step(steps, "generate_trade_intents", True, f"generated {len(result.trade_intents)} dry-run intents", {"count": len(result.trade_intents)})
    except Exception as exc:
        result.trade_intents = []
        result.metadata["no_intent_reason"] = "strategy generation failed"
        _record_step(steps, "generate_trade_intents", False, "strategy generation failed; no intents emitted", errors=[repr(exc)])


    if enable_portfolio_plan:
        try:
            from qmt_ai_trading.portfolio.allocator import PortfolioAllocationConfig
            from qmt_ai_trading.portfolio.rebalance import PortfolioRebalanceConfig
            from qmt_ai_trading.portfolio.service import build_portfolio_plan_from_candidates

            plan = build_portfolio_plan_from_candidates(
                result.candidates,
                run_id=ctx.run_id,
                total_asset=portfolio_total_asset,
                current_cash=portfolio_current_cash,
                snapshot_path=portfolio_snapshot_path,
                allocation_config=PortfolioAllocationConfig(
                    method=portfolio_method,
                    top_n=portfolio_top_n,
                    cash_reserve_ratio=portfolio_cash_reserve_ratio,
                    max_symbol_weight=portfolio_max_symbol_weight,
                    max_portfolio_weight=portfolio_max_weight,
                    min_score=min_score,
                ),
                rebalance_config=PortfolioRebalanceConfig(rebalance_threshold=portfolio_rebalance_threshold),
            )
            result.metadata["portfolio_plan"] = plan
            result.trade_intents = list(plan.trade_intents)
            _record_step(steps, "portfolio_plan", True, f"generated portfolio plan with {len(plan.targets)} targets and {len(plan.trade_intents)} dry-run intents", {"targets": len(plan.targets), "adjustments": len(plan.adjustments), "trade_intents": len(plan.trade_intents)})
        except Exception as exc:
            result.metadata["portfolio_plan_error"] = repr(exc)
            _record_step(steps, "portfolio_plan", False, "portfolio plan generation failed", errors=[repr(exc)])

    try:
        result.risk_decisions = [validate_trade_intent(intent) for intent in result.trade_intents]
        _record_step(steps, "risk_gate", True, f"validated {len(result.risk_decisions)} intents", {"count": len(result.risk_decisions)})
    except Exception as exc:
        result.risk_decisions = []
        _record_step(steps, "risk_gate", False, "risk validation failed", errors=[repr(exc)])

    try:
        result.shadow_replay_result = replay_trade_intents(result.trade_intents, prices=prices, initial_cash=initial_cash)
        result.backtest_result = result.shadow_replay_result.backtest_result
        _record_step(steps, "shadow_replay_backtest", True, "completed simulated shadow replay/backtest", dict(result.shadow_replay_result.report))
    except Exception as exc:
        _record_step(steps, "shadow_replay_backtest", False, "simulated shadow replay/backtest failed", errors=[repr(exc)])

    result.success = all(step.success for step in steps)

    if enable_agent_research:
        try:
            from pathlib import Path
            from qmt_ai_trading.agent.service import run_agent_research_from_pipeline_result, save_agent_research_memo
            from qmt_ai_trading.agent.summarizer import AgentSummarizerConfig

            memo = run_agent_research_from_pipeline_result(
                result,
                config=AgentSummarizerConfig(
                    mode=agent_research_mode,
                    include_monitoring=agent_include_monitoring,
                    include_backtest=agent_include_backtest,
                    include_human_checklist=agent_include_human_checklist,
                ),
            )
            out_dir = Path(agent_research_output_dir)
            md_path = out_dir / f"{ctx.run_id}.agent_research.md"
            json_path = out_dir / f"{ctx.run_id}.agent_research.json"
            save_agent_research_memo(memo, md_path)
            save_agent_research_memo(memo, json_path)
            result.metadata["agent_research"] = {
                "memo": memo,
                "memo_id": memo.memo_id,
                "mode": memo.mode,
                "success": memo.success,
                "executive_summary": memo.executive_summary,
                "risk_summary": memo.risk_summary,
                "human_review_checklist": memo.human_review_checklist,
                "safety_note": memo.safety_note,
                "output_path": str(md_path),
                "json_output_path": str(json_path),
            }
            _record_step(steps, "agent_research", memo.success, f"generated read-only Agent Research memo: {md_path}", {"output_path": str(md_path), "mode": memo.mode})
            result.success = all(step.success for step in steps)
        except Exception as exc:
            result.metadata["agent_research_error"] = repr(exc)
            _record_step(steps, "agent_research", False, "Agent Research generation failed", errors=[repr(exc)])
            result.success = all(step.success for step in steps)

    if enable_live_gray_readiness:
        try:
            from pathlib import Path
            from qmt_ai_trading.liveprep.safety import build_default_live_gray_config
            from qmt_ai_trading.liveprep.service import run_live_gray_readiness_check, save_live_gray_readiness_report
            ds = result.metadata.get("data_source", {}) if isinstance(result.metadata, dict) else {}
            agent_meta = result.metadata.get("agent_research") if isinstance(result.metadata, dict) else None
            cfg = build_default_live_gray_config(
                live_enabled=live_enabled, gray_enabled=live_gray_enabled,
                allowed_symbols=list(live_gray_allowed_symbols or ctx.symbols or []),
                max_total_capital=live_gray_max_total_capital,
                max_single_order_value=live_gray_max_single_order_value,
                max_symbol_weight=live_gray_max_symbol_weight,
                max_portfolio_weight=live_gray_max_portfolio_weight,
                operator_name=live_gray_operator_name,
                allow_unknown_quality_for_review=True,
                metadata={"pipeline_run_id": ctx.run_id},
            )
            report = run_live_gray_readiness_check(config=cfg, trade_intents=result.trade_intents, risk_decisions=result.risk_decisions, agent_memo=agent_meta, cache_quality_decision=ds, metadata={"pipeline_run_id": ctx.run_id})
            out_dir = Path(live_gray_output_dir); md_path = out_dir / f"{ctx.run_id}.live_gray.md"; json_path = out_dir / f"{ctx.run_id}.live_gray.json"
            save_live_gray_readiness_report(report, md_path); save_live_gray_readiness_report(report, json_path)
            result.metadata["live_gray_readiness"] = {"decision": getattr(report.decision, "value", report.decision), "summary": report.summary, "failed_checks": [c.to_dict() for c in report.checks if getattr(c.status, "value", c.status)=="FAIL"], "manual_review_items": report.manual_review_items, "safety_note": report.safety_note, "output_path": str(md_path), "json_output_path": str(json_path)}
            _record_step(steps, "live_gray_readiness", True, f"generated live gray readiness preparation report: {md_path}", {"output_path": str(md_path)})
        except Exception as exc:
            result.metadata["live_gray_readiness_error"] = repr(exc)
            _record_step(steps, "live_gray_readiness", False, "Live Gray Readiness generation failed", errors=[repr(exc)])
        result.success = all(step.success for step in steps)

    if enable_data_quality_tracking:
        try:
            from pathlib import Path
            from qmt_ai_trading.data_quality.service import run_data_quality_tracking, save_data_quality_tracking_report
            dq_symbols = list(data_quality_tracking_symbols or ctx.symbols or [])
            dq_report = run_data_quality_tracking(
                report_dir=data_quality_tracking_report_dir,
                cache_root=data_quality_tracking_cache_root,
                symbols=dq_symbols,
                start_date=data_quality_tracking_start or research_start_date or "",
                end_date=data_quality_tracking_end or research_end_date or str(ctx.trade_date),
                frequency=research_frequency,
                metadata={"pipeline_run_id": ctx.run_id},
            )
            out_dir = Path(data_quality_tracking_output_dir)
            md_path = out_dir / f"{ctx.run_id}.data_quality_tracking.md"
            json_path = out_dir / f"{ctx.run_id}.data_quality_tracking.json"
            save_data_quality_tracking_report(dq_report, md_path); save_data_quality_tracking_report(dq_report, json_path)
            result.metadata["data_quality_tracking"] = {"report_id": dq_report.report_id, "summary": dq_report.summary, "safety_note": dq_report.safety_note, "output_path": str(md_path), "json_output_path": str(json_path)}
            _record_step(steps, "data_quality_tracking", True, f"generated read-only Data Quality Tracking report: {md_path}", {"output_path": str(md_path)})
        except Exception as exc:
            result.metadata["data_quality_tracking_error"] = repr(exc)
            _record_step(steps, "data_quality_tracking", False, "Data Quality Tracking generation failed", errors=[repr(exc)])
        result.success = all(step.success for step in steps)

    if enable_notification_dry_run:
        try:
            from pathlib import Path
            from qmt_ai_trading.notification_dryrun.service import run_notification_dry_run, save_notification_dry_run_report
            summaries = {"daily_report": {"run_id": ctx.run_id, "success": result.success, "steps": len(steps)}}
            if "agent_research" in result.metadata: summaries["agent_memo"] = result.metadata["agent_research"]
            if "live_gray_readiness" in result.metadata: summaries["live_gray_report"] = result.metadata["live_gray_readiness"]
            if "data_quality_tracking" in result.metadata: summaries["data_quality_report"] = result.metadata["data_quality_tracking"]
            out_dir = Path(notification_dry_run_output_dir)
            md_path = out_dir / f"{ctx.run_id}.notification_dryrun.md"
            json_path = out_dir / f"{ctx.run_id}.notification_dryrun.json"
            report = run_notification_dry_run(summaries=summaries, channels=notification_dry_run_channels, recipients=notification_dry_run_recipients, output_path=md_path, json_output_path=json_path, preview_output_dir=notification_dry_run_preview_output_dir, metadata={"pipeline_run_id": ctx.run_id})
            result.metadata["notification_dry_run"] = {"report_id": report.report_id, "success": report.success, "summary": report.summary, "safety_note": report.safety_note, "output_path": str(md_path), "json_output_path": str(json_path)}
            _record_step(steps, "notification_dry_run", True, f"generated notification dry-run report: {md_path}", {"output_path": str(md_path)})
        except Exception as exc:
            result.metadata["notification_dry_run_error"] = repr(exc)
            _record_step(steps, "notification_dry_run", False, "Notification Dry Run generation failed", errors=[repr(exc)])
        result.success = all(step.success for step in steps)

    if enable_gray_rehearsal:
        try:
            from pathlib import Path
            from qmt_ai_trading.gray_rehearsal.safety import build_default_gray_rehearsal_config
            from qmt_ai_trading.gray_rehearsal.service import run_gray_rehearsal, save_gray_rehearsal_report
            cfg = build_default_gray_rehearsal_config(
                allowed_symbols=list(gray_rehearsal_allowed_symbols or ctx.symbols or []),
                max_total_capital=gray_rehearsal_max_total_capital,
                max_single_order_value=gray_rehearsal_max_single_order_value,
                metadata={"pipeline_run_id": ctx.run_id, "live_enabled": False, "real_send_enabled": False, "external_network_enabled": False},
            )
            rehearsal_context = {
                "pipeline_report": "in-memory pipeline result",
                "monitoring_report": result.metadata.get("monitoring") or result.metadata.get("monitoring_report"),
                "data_quality_report": result.metadata.get("data_quality_tracking"),
                "agent_memo": result.metadata.get("agent_research"),
                "live_gray_report": result.metadata.get("live_gray_readiness"),
                "notification_dry_run_report": result.metadata.get("notification_dry_run"),
                "dashboard_path": result.metadata.get("dashboard_path", ""),
            }
            rehearsal = run_gray_rehearsal(config=cfg, context=rehearsal_context, metadata={"pipeline_run_id": ctx.run_id})
            out_dir = Path(gray_rehearsal_output_dir)
            md_path = out_dir / f"{ctx.run_id}.gray_rehearsal.md"
            json_path = out_dir / f"{ctx.run_id}.gray_rehearsal.json"
            save_gray_rehearsal_report(rehearsal, md_path); save_gray_rehearsal_report(rehearsal, json_path)
            result.metadata["gray_rehearsal"] = {"report_id": rehearsal.report_id, "decision": getattr(rehearsal.decision, "value", rehearsal.decision), "summary": rehearsal.summary, "safety_note": rehearsal.safety_note, "output_path": str(md_path), "json_output_path": str(json_path)}
            _record_step(steps, "gray_rehearsal", True, f"generated gray rehearsal dry-run report: {md_path}", {"output_path": str(md_path)})
        except Exception as exc:
            result.metadata["gray_rehearsal_error"] = repr(exc)
            _record_step(steps, "gray_rehearsal", False, "Gray Rehearsal generation failed", errors=[repr(exc)])
        result.success = all(step.success for step in steps)


    if enable_gray_decision_package:
        try:
            from pathlib import Path
            from qmt_ai_trading.gray_decision.safety import build_default_gray_decision_config
            from qmt_ai_trading.gray_decision.service import run_gray_decision_package, save_gray_decision_package
            from qmt_ai_trading.gray_decision.evidence import collect_evidence_from_file
            from qmt_ai_trading.gray_decision.models import GrayDecisionEvidenceType
            cfg = build_default_gray_decision_config(
                allowed_symbols=list(gray_decision_allowed_symbols or ctx.symbols or []),
                max_total_capital=gray_decision_max_total_capital,
                max_single_order_value=gray_decision_max_single_order_value,
                max_symbol_weight=gray_decision_max_symbol_weight,
                max_portfolio_weight=gray_decision_max_portfolio_weight,
                operator_name=gray_decision_operator_name,
                reviewer_name=gray_decision_reviewer_name,
                metadata={"pipeline_run_id": ctx.run_id},
            )
            ev=[]
            local_paths=[
                (result.metadata.get("agent_research",{}).get("output_path") if isinstance(result.metadata.get("agent_research"),dict) else None, GrayDecisionEvidenceType.AGENT_RESEARCH),
                (result.metadata.get("live_gray_readiness",{}).get("output_path") if isinstance(result.metadata.get("live_gray_readiness"),dict) else None, GrayDecisionEvidenceType.LIVE_GRAY_READINESS),
                (result.metadata.get("data_quality_tracking",{}).get("output_path") if isinstance(result.metadata.get("data_quality_tracking"),dict) else None, GrayDecisionEvidenceType.DATA_QUALITY),
                (result.metadata.get("notification_dry_run",{}).get("output_path") if isinstance(result.metadata.get("notification_dry_run"),dict) else None, GrayDecisionEvidenceType.NOTIFICATION_DRY_RUN),
                (result.metadata.get("gray_rehearsal",{}).get("output_path") if isinstance(result.metadata.get("gray_rehearsal"),dict) else None, GrayDecisionEvidenceType.GRAY_REHEARSAL),
                (result.metadata.get("dashboard_path"), GrayDecisionEvidenceType.DASHBOARD),
            ]
            for path, et in local_paths:
                ev.append(collect_evidence_from_file(path, et))
            package = run_gray_decision_package(config=cfg, evidence=ev, metadata={"pipeline_run_id": ctx.run_id})
            out_dir = Path(gray_decision_output_dir); md_path = out_dir / f"{ctx.run_id}.gray_decision.md"; json_path = out_dir / f"{ctx.run_id}.gray_decision.json"
            save_gray_decision_package(package, md_path); save_gray_decision_package(package, json_path)
            result.metadata["gray_decision_package"] = {"package_id": package.package_id, "decision": getattr(package.decision, "value", package.decision), "output_path": str(md_path), "json_output_path": str(json_path), "warnings": package.warnings, "blocked_reasons": package.blocked_reasons, "safety_note": package.safety_note}
            _record_step(steps, "gray_decision_package", True, f"generated manual-only gray decision package: {md_path}", {"output_path": str(md_path)})
        except Exception as exc:
            result.metadata["gray_decision_package_error"] = repr(exc)
            _record_step(steps, "gray_decision_package", False, "Gray Decision Package generation failed", errors=[repr(exc)])
        result.success = all(step.success for step in steps)


    if enable_live_manual_prep:
        try:
            from pathlib import Path
            from qmt_ai_trading.live_manual_prep.safety import build_default_live_manual_prep_config
            from qmt_ai_trading.live_manual_prep.service import run_live_manual_prep_package_from_files, save_live_manual_prep_package
            cfg = build_default_live_manual_prep_config(
                allowed_symbols=list(live_manual_prep_allowed_symbols or ctx.symbols or []),
                max_total_capital=live_manual_prep_max_total_capital,
                max_single_order_value=live_manual_prep_max_single_order_value,
                max_symbol_weight=live_manual_prep_max_symbol_weight,
                max_portfolio_weight=live_manual_prep_max_portfolio_weight,
                operator_name=live_manual_prep_operator_name,
                reviewer_name=live_manual_prep_reviewer_name,
                risk_owner_name=live_manual_prep_risk_owner_name,
                metadata={"pipeline_run_id": ctx.run_id},
            )
            package = run_live_manual_prep_package_from_files(
                config=cfg,
                gray_decision_package=(result.metadata.get("gray_decision_package",{}) or {}).get("output_path") if isinstance(result.metadata.get("gray_decision_package"),dict) else None,
                live_gray_report=(result.metadata.get("live_gray_readiness",{}) or {}).get("output_path") if isinstance(result.metadata.get("live_gray_readiness"),dict) else None,
                gray_rehearsal_report=(result.metadata.get("gray_rehearsal",{}) or {}).get("output_path") if isinstance(result.metadata.get("gray_rehearsal"),dict) else None,
                pipeline_report=None,
                monitoring_report=(result.metadata.get("monitoring",{}) or {}).get("output_path") if isinstance(result.metadata.get("monitoring"),dict) else None,
                data_quality_report=(result.metadata.get("data_quality_tracking",{}) or {}).get("output_path") if isinstance(result.metadata.get("data_quality_tracking"),dict) else None,
                agent_memo=(result.metadata.get("agent_research",{}) or {}).get("output_path") if isinstance(result.metadata.get("agent_research"),dict) else None,
                notification_dry_run_report=(result.metadata.get("notification_dry_run",{}) or {}).get("output_path") if isinstance(result.metadata.get("notification_dry_run"),dict) else None,
                dashboard_path=result.metadata.get("dashboard_path"),
            )
            out_dir = Path(live_manual_prep_output_dir); md_path = out_dir / f"{ctx.run_id}.live_manual_prep.md"; json_path = out_dir / f"{ctx.run_id}.live_manual_prep.json"
            save_live_manual_prep_package(package, md_path); save_live_manual_prep_package(package, json_path)
            result.metadata["live_manual_prep"] = {"package_id": package.package_id, "decision": getattr(package.decision, "value", package.decision), "output_path": str(md_path), "json_output_path": str(json_path), "warnings": package.warnings, "blocked_reasons": package.blocked_reasons, "safety_note": package.safety_note}
            _record_step(steps, "live_manual_prep", True, f"generated preparation-only live manual approval prep package: {md_path}", {"output_path": str(md_path)})
        except Exception as exc:
            result.metadata["live_manual_prep_error"] = repr(exc)
            _record_step(steps, "live_manual_prep", False, "Live Manual Approval Prep generation failed", errors=[repr(exc)])
        result.success = all(step.success for step in steps)

    if enable_live_env_check:
        try:
            from pathlib import Path
            from qmt_ai_trading.live_env_check.safety import build_default_live_env_check_config
            from qmt_ai_trading.live_env_check.service import run_live_env_check_from_files, save_live_env_check_report
            cfg = build_default_live_env_check_config(
                allowed_symbols=list(live_env_check_allowed_symbols or ctx.symbols or []),
                max_total_capital=live_env_check_max_total_capital,
                max_single_order_value=live_env_check_max_single_order_value,
                max_symbol_weight=live_env_check_max_symbol_weight,
                max_portfolio_weight=live_env_check_max_portfolio_weight,
                operator_name=live_env_check_operator_name,
                reviewer_name=live_env_check_reviewer_name,
                metadata={"pipeline_run_id": ctx.run_id, "live_enabled": False, "real_order_enabled": False, "real_send_enabled": False},
            )
            report = run_live_env_check_from_files(
                repo_root=Path.cwd(),
                config=cfg,
                dashboard_path=result.metadata.get("dashboard_path"),
                notification_dry_run_report=(result.metadata.get("notification_dry_run", {}) or {}).get("output_path") if isinstance(result.metadata.get("notification_dry_run"), dict) else None,
                data_quality_report=(result.metadata.get("data_quality_tracking", {}) or {}).get("output_path") if isinstance(result.metadata.get("data_quality_tracking"), dict) else None,
                agent_memo=(result.metadata.get("agent_research", {}) or {}).get("output_path") if isinstance(result.metadata.get("agent_research"), dict) else None,
                live_manual_prep_package=(result.metadata.get("live_manual_prep", {}) or {}).get("output_path") if isinstance(result.metadata.get("live_manual_prep"), dict) else None,
                gray_decision_package=(result.metadata.get("gray_decision_package", {}) or {}).get("output_path") if isinstance(result.metadata.get("gray_decision_package"), dict) else None,
                metadata={"pipeline_run_id": ctx.run_id},
            )
            out_dir = Path(live_env_check_output_dir); md_path = out_dir / f"{ctx.run_id}.live_env_check.md"; json_path = out_dir / f"{ctx.run_id}.live_env_check.json"
            save_live_env_check_report(report, md_path); save_live_env_check_report(report, json_path)
            result.metadata["live_env_check"] = {"report_id": report.report_id, "decision": getattr(report.decision, "value", report.decision), "output_path": str(md_path), "json_output_path": str(json_path), "warnings": report.warnings, "blocked_reasons": report.blocked_reasons, "safety_note": report.safety_note}
            _record_step(steps, "live_env_check", True, f"generated Live Environment Read-only Check Report: {md_path}", {"output_path": str(md_path)})
        except Exception as exc:
            result.metadata["live_env_check_error"] = repr(exc)
            _record_step(steps, "live_env_check", False, "Live Environment Check generation failed", errors=[repr(exc)])
        result.success = all(step.success for step in steps)

    from qmt_ai_trading.pipeline.report import format_pipeline_report

    result.report_text = format_pipeline_report(result)
    return result


def run_etf_daily_pipeline(
    *,
    trade_date: date | str | None = None,
    symbols: Iterable[str] | None = None,
    dry_run: bool = True,
    prices: Mapping[str, float] | None = None,
    score_by_symbol: Mapping[str, float] | None = None,
    top_n: int = 1,
    min_score: float | None = None,
    capital: float | None = None,
    initial_cash: float = 1_000_000.0,
    use_cached_research: bool = False,
    cache_root: str = "market_data",
    research_start_date: str | None = None,
    research_end_date: str | None = None,
    research_frequency: str = "1d",
    min_bars: int = 20,
    allow_partial_research: bool = True,
    cached_strategy_top_n: int = 1,
    cached_strategy_min_score: float | None = None,
    cached_strategy_min_bars: int = 20,
    data_source_mode: str = "cached_real_first",
    quality_report_dir: str = "qmt_data_quality_reports",
    require_quality_report: bool = False,
    allow_unknown_quality_for_dry_run: bool = True,
    allow_mock_cache: bool = False,
    min_quality_level: str = "UNKNOWN",
    allow_mock_fallback: bool = False,
    min_coverage_ratio: float = 0.8,
    min_loaded_symbols: int = 1,
    require_cached_research: bool = False,
    data_source_confidence_required: str | None = None,
    enable_portfolio_plan: bool = False,
    portfolio_method: str = "score_weight",
    portfolio_top_n: int = 2,
    portfolio_cash_reserve_ratio: float = 0.2,
    portfolio_max_symbol_weight: float = 0.3,
    portfolio_max_weight: float = 0.8,
    portfolio_rebalance_threshold: float = 0.05,
    portfolio_total_asset: float = 1_000_000.0,
    portfolio_current_cash: float = 1_000_000.0,
    portfolio_snapshot_path: str | None = None,
    enable_agent_research: bool = False,
    agent_research_output_dir: str = "agent_reports",
    agent_research_mode: str = "local_rules",
    agent_include_monitoring: bool = True,
    agent_include_backtest: bool = True,
    agent_include_human_checklist: bool = True,
    enable_live_gray_readiness: bool = False,
    live_gray_output_dir: str = "live_gray_reports",
    live_gray_allowed_symbols: Iterable[str] | None = None,
    live_gray_max_total_capital: float = 5000.0,
    live_gray_max_single_order_value: float = 1000.0,
    live_gray_max_symbol_weight: float = 0.1,
    live_gray_max_portfolio_weight: float = 0.2,
    live_gray_enabled: bool = False,
    live_enabled: bool = False,
    live_gray_operator_name: str = "",
    enable_data_quality_tracking: bool = False,
    data_quality_tracking_output_dir: str = "data_quality_tracking",
    data_quality_tracking_report_dir: str = "qmt_data_quality_reports",
    data_quality_tracking_cache_root: str | None = None,
    data_quality_tracking_symbols: Iterable[str] | None = None,
    data_quality_tracking_start: str | None = None,
    data_quality_tracking_end: str | None = None,
    enable_notification_dry_run: bool = False,
    notification_dry_run_output_dir: str = "notification_dryrun",
    notification_dry_run_channels: Iterable[str] | str | None = None,
    notification_dry_run_recipients: Iterable[str] | str | None = None,
    notification_dry_run_preview_output_dir: str | None = None,
    enable_gray_rehearsal: bool = False,
    gray_rehearsal_output_dir: str = "gray_rehearsal",
    gray_rehearsal_allowed_symbols: Iterable[str] | None = None,
    gray_rehearsal_max_total_capital: float = 5000.0,
    gray_rehearsal_max_single_order_value: float = 1000.0,
    enable_gray_decision_package: bool = False,
    gray_decision_output_dir: str = "gray_decision",
    gray_decision_allowed_symbols: Iterable[str] | None = None,
    gray_decision_max_total_capital: float = 5000.0,
    gray_decision_max_single_order_value: float = 1000.0,
    gray_decision_max_symbol_weight: float = 0.1,
    gray_decision_max_portfolio_weight: float = 0.2,
    gray_decision_operator_name: str = "",
    gray_decision_reviewer_name: str = "",
    enable_live_manual_prep: bool = False,
    live_manual_prep_output_dir: str = "live_manual_prep",
    live_manual_prep_allowed_symbols: Iterable[str] | None = None,
    live_manual_prep_max_total_capital: float = 5000.0,
    live_manual_prep_max_single_order_value: float = 1000.0,
    live_manual_prep_max_symbol_weight: float = 0.1,
    live_manual_prep_max_portfolio_weight: float = 0.2,
    live_manual_prep_operator_name: str = "",
    live_manual_prep_reviewer_name: str = "",
    live_manual_prep_risk_owner_name: str = "",
    enable_live_env_check: bool = False,
    live_env_check_output_dir: str = "live_env_check",
    live_env_check_allowed_symbols: Iterable[str] | None = None,
    live_env_check_max_total_capital: float = 5000.0,
    live_env_check_max_single_order_value: float = 1000.0,
    live_env_check_max_symbol_weight: float = 0.1,
    live_env_check_max_portfolio_weight: float = 0.2,
    live_env_check_operator_name: str = "",
    live_env_check_reviewer_name: str = "",
) -> PipelineResult:
    """Run the default ETF daily pipeline using the Data Hub ETF universe."""

    universe = get_default_etf_universe()
    symbol_filter = {normalize_symbol(item) for item in (symbols or []) if str(item).strip()}
    if symbol_filter:
        universe = [item for item in universe if normalize_symbol(item.symbol) in symbol_filter]
    context = build_pipeline_context(trade_date, dry_run=dry_run, symbols=symbol_filter or [item.symbol for item in universe], metadata={"pipeline": "etf_daily", "simulated_only": True})
    if use_cached_research and data_source_mode == "cached_real_first":
        data_source_mode = "cached"
    effective_cached = use_cached_research or data_source_mode in {"cached", "auto", "cached_real_first"}
    candidates = None if effective_cached else build_candidates_from_universe(universe, score_by_symbol=score_by_symbol, default_score=0.0, target_percent=None)
    return run_daily_signal_pipeline(
        context=context,
        candidates=candidates,
        prices=prices,
        top_n=top_n,
        min_score=min_score,
        capital=capital,
        initial_cash=initial_cash,
        use_cached_research=use_cached_research,
        data_source_mode=data_source_mode,
        quality_report_dir=quality_report_dir,
        require_quality_report=require_quality_report,
        allow_unknown_quality_for_dry_run=allow_unknown_quality_for_dry_run,
        allow_mock_cache=allow_mock_cache,
        min_quality_level=min_quality_level,
        allow_mock_fallback=allow_mock_fallback,
        min_coverage_ratio=min_coverage_ratio,
        min_loaded_symbols=min_loaded_symbols,
        require_cached_research=require_cached_research,
        data_source_confidence_required=data_source_confidence_required,
        cache_root=cache_root,
        research_start_date=research_start_date,
        research_end_date=research_end_date,
        research_frequency=research_frequency,
        min_bars=min_bars,
        allow_partial_research=allow_partial_research,
        cached_strategy_top_n=cached_strategy_top_n,
        cached_strategy_min_score=cached_strategy_min_score,
        cached_strategy_min_bars=cached_strategy_min_bars,
        enable_portfolio_plan=enable_portfolio_plan,
        portfolio_method=portfolio_method,
        portfolio_top_n=portfolio_top_n,
        portfolio_cash_reserve_ratio=portfolio_cash_reserve_ratio,
        portfolio_max_symbol_weight=portfolio_max_symbol_weight,
        portfolio_max_weight=portfolio_max_weight,
        portfolio_rebalance_threshold=portfolio_rebalance_threshold,
        portfolio_total_asset=portfolio_total_asset,
        portfolio_current_cash=portfolio_current_cash,
        portfolio_snapshot_path=portfolio_snapshot_path,
        enable_agent_research=enable_agent_research,
        agent_research_output_dir=agent_research_output_dir,
        agent_research_mode=agent_research_mode,
        agent_include_monitoring=agent_include_monitoring,
        agent_include_backtest=agent_include_backtest,
        agent_include_human_checklist=agent_include_human_checklist,
        enable_live_gray_readiness=enable_live_gray_readiness,
        live_gray_output_dir=live_gray_output_dir,
        live_gray_allowed_symbols=live_gray_allowed_symbols,
        live_gray_max_total_capital=live_gray_max_total_capital,
        live_gray_max_single_order_value=live_gray_max_single_order_value,
        live_gray_max_symbol_weight=live_gray_max_symbol_weight,
        live_gray_max_portfolio_weight=live_gray_max_portfolio_weight,
        live_gray_enabled=live_gray_enabled,
        live_enabled=live_enabled,
        live_gray_operator_name=live_gray_operator_name,
        enable_data_quality_tracking=enable_data_quality_tracking,
        data_quality_tracking_output_dir=data_quality_tracking_output_dir,
        data_quality_tracking_report_dir=data_quality_tracking_report_dir,
        data_quality_tracking_cache_root=data_quality_tracking_cache_root,
        data_quality_tracking_symbols=data_quality_tracking_symbols,
        data_quality_tracking_start=data_quality_tracking_start,
        data_quality_tracking_end=data_quality_tracking_end,
        enable_notification_dry_run=enable_notification_dry_run,
        notification_dry_run_output_dir=notification_dry_run_output_dir,
        notification_dry_run_channels=notification_dry_run_channels,
        notification_dry_run_recipients=notification_dry_run_recipients,
        notification_dry_run_preview_output_dir=notification_dry_run_preview_output_dir,
        enable_gray_rehearsal=enable_gray_rehearsal,
        gray_rehearsal_output_dir=gray_rehearsal_output_dir,
        gray_rehearsal_allowed_symbols=gray_rehearsal_allowed_symbols,
        gray_rehearsal_max_total_capital=gray_rehearsal_max_total_capital,
        gray_rehearsal_max_single_order_value=gray_rehearsal_max_single_order_value,
        enable_gray_decision_package=enable_gray_decision_package,
        gray_decision_output_dir=gray_decision_output_dir,
        gray_decision_allowed_symbols=gray_decision_allowed_symbols,
        gray_decision_max_total_capital=gray_decision_max_total_capital,
        gray_decision_max_single_order_value=gray_decision_max_single_order_value,
        gray_decision_max_symbol_weight=gray_decision_max_symbol_weight,
        gray_decision_max_portfolio_weight=gray_decision_max_portfolio_weight,
        gray_decision_operator_name=gray_decision_operator_name,
        gray_decision_reviewer_name=gray_decision_reviewer_name,
        enable_live_manual_prep=enable_live_manual_prep,
        live_manual_prep_output_dir=live_manual_prep_output_dir,
        live_manual_prep_allowed_symbols=live_manual_prep_allowed_symbols,
        live_manual_prep_max_total_capital=live_manual_prep_max_total_capital,
        live_manual_prep_max_single_order_value=live_manual_prep_max_single_order_value,
        live_manual_prep_max_symbol_weight=live_manual_prep_max_symbol_weight,
        live_manual_prep_max_portfolio_weight=live_manual_prep_max_portfolio_weight,
        live_manual_prep_operator_name=live_manual_prep_operator_name,
        live_manual_prep_reviewer_name=live_manual_prep_reviewer_name,
        live_manual_prep_risk_owner_name=live_manual_prep_risk_owner_name,
        enable_live_env_check=enable_live_env_check,
        live_env_check_output_dir=live_env_check_output_dir,
        live_env_check_allowed_symbols=live_env_check_allowed_symbols,
        live_env_check_max_total_capital=live_env_check_max_total_capital,
        live_env_check_max_single_order_value=live_env_check_max_single_order_value,
        live_env_check_max_symbol_weight=live_env_check_max_symbol_weight,
        live_env_check_max_portfolio_weight=live_env_check_max_portfolio_weight,
        live_env_check_operator_name=live_env_check_operator_name,
        live_env_check_reviewer_name=live_env_check_reviewer_name,
    )
