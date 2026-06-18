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
) -> PipelineResult:
    """Run the generic daily signal pipeline without connecting to real QMT trading."""

    ctx = context or build_pipeline_context(dry_run=True)
    if not ctx.dry_run:
        ctx.dry_run = True
        ctx.metadata["dry_run_forced"] = True
    steps: list[PipelineStepResult] = []
    result = PipelineResult(context=ctx, steps=steps)

    if use_cached_research and candidates is None:
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
        if result.trade_intents:
            pass
        else:
            result.trade_intents = generate_etf_rotation_intents(result.candidates, top_n=top_n, min_score=min_score, dry_run=True, capital=capital or initial_cash)
        if not result.trade_intents:
            result.metadata["no_intent_reason"] = "no eligible candidates after strategy selection"
        _record_step(steps, "generate_trade_intents", True, f"generated {len(result.trade_intents)} dry-run intents", {"count": len(result.trade_intents)})
    except Exception as exc:
        result.trade_intents = []
        result.metadata["no_intent_reason"] = "strategy generation failed"
        _record_step(steps, "generate_trade_intents", False, "strategy generation failed; no intents emitted", errors=[repr(exc)])

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
) -> PipelineResult:
    """Run the default ETF daily pipeline using the Data Hub ETF universe."""

    universe = get_default_etf_universe()
    symbol_filter = {normalize_symbol(item) for item in (symbols or []) if str(item).strip()}
    if symbol_filter:
        universe = [item for item in universe if normalize_symbol(item.symbol) in symbol_filter]
    context = build_pipeline_context(trade_date, dry_run=dry_run, symbols=symbol_filter or [item.symbol for item in universe], metadata={"pipeline": "etf_daily", "simulated_only": True})
    candidates = None if use_cached_research else build_candidates_from_universe(universe, score_by_symbol=score_by_symbol, default_score=0.0, target_percent=None)
    return run_daily_signal_pipeline(
        context=context,
        candidates=candidates,
        prices=prices,
        top_n=top_n,
        min_score=min_score,
        capital=capital,
        initial_cash=initial_cash,
        use_cached_research=use_cached_research,
        cache_root=cache_root,
        research_start_date=research_start_date,
        research_end_date=research_end_date,
        research_frequency=research_frequency,
        min_bars=min_bars,
        allow_partial_research=allow_partial_research,
        cached_strategy_top_n=cached_strategy_top_n,
        cached_strategy_min_score=cached_strategy_min_score,
        cached_strategy_min_bars=cached_strategy_min_bars,
    )
