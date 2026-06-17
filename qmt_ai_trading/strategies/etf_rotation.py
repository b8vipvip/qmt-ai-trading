"""Standardized ETF rotation Strategy Engine outputs.

This module transforms already prepared ETF candidates into structured
``TradeIntent`` objects. It does not connect to QMT, does not submit orders, and
keeps real execution behind the project Risk Gate and QMT Gateway.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from qmt_ai_trading.common.types import TradeIntent
from qmt_ai_trading.config.settings import get_settings
from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.datahub.models import ETFUniverseItem
from qmt_ai_trading.datahub.symbols import normalize_symbol

DEFAULT_SOURCE = "etf_rotation"
LOT_SIZE = 100


@dataclass(slots=True)
class ETFCandidate:
    """Normalized ETF candidate consumed by the Strategy Engine."""

    symbol: str
    score: float = 0.0
    last_price: float | None = None
    target_percent: float | None = None
    name: str = ""
    eligible: bool = True
    reason: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ETFRotationDecision:
    """Selection decision before conversion to one or more TradeIntents."""

    selected: list[ETFCandidate] = field(default_factory=list)
    rejected: list[ETFCandidate] = field(default_factory=list)
    reason: str = ""
    source: str = DEFAULT_SOURCE
    dry_run: bool = True


def _candidate_from_mapping(row: Mapping[str, Any]) -> ETFCandidate:
    symbol = str(row.get("symbol") or row.get("stock_code") or row.get("code") or "").strip()
    raw_score = row.get("score", 0.0)
    raw_price = row.get("last_price", row.get("last_close"))
    raw_target = row.get("target_percent", row.get("target_position_pct"))
    metrics = {
        key: value
        for key, value in row.items()
        if key
        not in {
            "symbol",
            "stock_code",
            "code",
            "score",
            "last_price",
            "last_close",
            "target_percent",
            "target_position_pct",
            "stock_name",
            "name",
            "eligible",
            "skip_reason",
            "reason",
        }
    }
    return ETFCandidate(
        symbol=symbol,
        score=float(raw_score or 0.0),
        last_price=float(raw_price) if raw_price not in (None, "") else None,
        target_percent=float(raw_target) if raw_target not in (None, "") else None,
        name=str(row.get("name") or row.get("stock_name") or ""),
        eligible=bool(row.get("eligible", True)),
        reason=str(row.get("reason") or row.get("skip_reason") or ""),
        metrics=metrics,
    )


def _normalize_candidate(candidate: ETFCandidate | Mapping[str, Any]) -> ETFCandidate:
    if isinstance(candidate, ETFCandidate):
        return candidate
    return _candidate_from_mapping(candidate)


def _adapter_score_candidate(candidate: ETFCandidate, score_adapter: Any | None) -> ETFCandidate:
    """Optionally reuse existing research scoring without coupling to QMT.

    ``data_tools.etf_rotation_selector.score_etf`` remains the richer historical
    scoring implementation. Stage 4 accepts its output through mapping rows, or
    callers can pass a lightweight adapter for preloaded data. If no adapter is
    provided, the candidate's existing score is preserved.
    """

    if score_adapter is None:
        return candidate
    scored = score_adapter(candidate)
    if scored is None:
        return candidate
    return _normalize_candidate(scored)


def build_candidates_from_universe(
    universe: Iterable[ETFUniverseItem | Mapping[str, Any]] | None = None,
    *,
    score_by_symbol: Mapping[str, float] | None = None,
    default_score: float = 0.0,
    target_percent: float | None = None,
) -> list[ETFCandidate]:
    """Build Strategy Engine ETF candidates from the Data Hub ETF universe.

    The adapter is offline/read-only: it does not connect to QMT and does not
    place orders. External research layers may pass ``score_by_symbol`` to reuse
    their own scoring while keeping universe access behind Data Hub.
    """

    items = list(universe) if universe is not None else get_default_etf_universe()
    scores = {normalize_symbol(key): float(value) for key, value in (score_by_symbol or {}).items()}
    candidates: list[ETFCandidate] = []
    for item in items:
        if isinstance(item, ETFUniverseItem):
            symbol = normalize_symbol(item.symbol)
            enabled = item.enabled
            name = item.name
            metrics = {"category": item.category, "weight": item.weight, "universe_source": item.source}
        else:
            symbol = normalize_symbol(str(item.get("symbol") or item.get("code") or item.get("stock_code") or ""))
            enabled = bool(item.get("enabled", True))
            name = str(item.get("name") or item.get("stock_name") or "")
            metrics = {key: value for key, value in item.items() if key not in {"symbol", "code", "stock_code", "enabled", "name", "stock_name"}}
        candidates.append(
            ETFCandidate(
                symbol=symbol,
                score=scores.get(symbol, float(default_score)),
                target_percent=target_percent,
                name=name,
                eligible=enabled,
                reason="" if enabled else "disabled in Data Hub ETF universe",
                metrics=metrics,
            )
        )
    return candidates


def build_candidates_from_research_scores(
    scores: Iterable[Any],
    *,
    target_percent: float | None = None,
    min_score: float | None = None,
) -> list[ETFCandidate]:
    """Adapt ResearchScore objects into ETF candidates without placing orders.

    This adapter keeps Stage 6 Research output read-only. The returned
    candidates still flow through the existing ETF rotation selection and
    TradeIntent generation path, and execution remains behind Risk Gate and QMT
    Gateway.
    """

    candidates: list[ETFCandidate] = []
    for score in scores or []:
        symbol = normalize_symbol(str(getattr(score, "symbol", "")))
        raw_score = getattr(score, "score", None)
        numeric_score = float(raw_score) if raw_score is not None else 0.0
        eligible = bool(getattr(score, "eligible", True)) and bool(symbol)
        reason = str(getattr(score, "reason", "") or "")
        if raw_score is None:
            eligible = False
            reason = reason or "research score unavailable"
        if min_score is not None and numeric_score < float(min_score):
            eligible = False
            reason = reason or f"research score below min_score {float(min_score):.2f}"
        metrics = dict(getattr(score, "metrics", {}) or {})
        metrics["research_score"] = raw_score
        candidates.append(
            ETFCandidate(
                symbol=symbol,
                score=numeric_score,
                target_percent=target_percent,
                eligible=eligible,
                reason=reason,
                metrics=metrics,
            )
        )
    return candidates


def score_etf_candidates(
    candidates: Iterable[ETFCandidate | Mapping[str, Any]],
    *,
    score_adapter: Any | None = None,
    min_score: float | None = None,
) -> list[ETFCandidate]:
    """Normalize and score ETF candidates, preserving legacy scoring adapters."""

    scored: list[ETFCandidate] = []
    for raw in candidates or []:
        candidate = _adapter_score_candidate(_normalize_candidate(raw), score_adapter)
        if min_score is not None and candidate.score < float(min_score):
            candidate.eligible = False
            candidate.reason = candidate.reason or f"score below min_score {float(min_score):.2f}"
        scored.append(candidate)
    return scored


def select_top_etfs(
    candidates: Sequence[ETFCandidate | Mapping[str, Any]],
    *,
    top_n: int = 1,
    min_score: float | None = None,
) -> ETFRotationDecision:
    """Select eligible ETFs by descending score without placing orders."""

    normalized = score_etf_candidates(candidates, min_score=min_score)
    eligible = [item for item in normalized if item.eligible and item.symbol]
    rejected = [item for item in normalized if item not in eligible]
    eligible.sort(key=lambda item: item.score, reverse=True)
    selected = eligible[: max(1, int(top_n or 1))]
    if not normalized:
        reason = "no ETF candidates provided; HOLD/no intents"
    elif not selected:
        reason = "no eligible ETF candidates after scoring filters; HOLD/no intents"
    else:
        reason = "selected top ETF candidates by score"
    return ETFRotationDecision(selected=selected, rejected=rejected, reason=reason)


def _cap_target_percent(value: float | None) -> float:
    settings = get_settings()
    requested = settings.max_position_pct if value is None else float(value)
    return max(0.0, min(requested, settings.max_position_pct))


def _buy_quantity(candidate: ETFCandidate, target_percent: float, capital: float | None) -> int:
    if not candidate.last_price or candidate.last_price <= 0 or not capital or capital <= 0:
        return LOT_SIZE
    raw_quantity = int((float(capital) * target_percent) / candidate.last_price)
    lots = raw_quantity // LOT_SIZE
    return max(LOT_SIZE, lots * LOT_SIZE)


def generate_etf_rotation_signal(
    candidates: Iterable[ETFCandidate | Mapping[str, Any]] | None = None,
    *,
    symbol: str | None = None,
    top_n: int = 1,
    min_score: float | None = None,
    dry_run: bool = True,
    source: str = DEFAULT_SOURCE,
    capital: float | None = None,
) -> TradeIntent:
    """Return one standardized ETF rotation TradeIntent, defaulting to dry-run."""

    if candidates is None:
        candidates = [ETFCandidate(symbol=symbol or "510300.SH", eligible=False, reason="no candidate data supplied")]
    decision = select_top_etfs(list(candidates), top_n=top_n, min_score=min_score)
    if not decision.selected:
        return TradeIntent(
            symbol=symbol or "ETF_ROTATION",
            side="HOLD",
            quantity=0,
            target_percent=0.0,
            reason=decision.reason,
            source=source,
            dry_run=dry_run,
        )
    candidate = decision.selected[0]
    target_percent = _cap_target_percent(candidate.target_percent)
    return TradeIntent(
        symbol=candidate.symbol,
        side="BUY",
        quantity=_buy_quantity(candidate, target_percent, capital),
        target_percent=target_percent,
        reason=f"{decision.reason}; {candidate.symbol} score={candidate.score:.2f}",
        source=source,
        dry_run=dry_run,
    )


def generate_etf_rotation_intents(
    candidates: Iterable[ETFCandidate | Mapping[str, Any]],
    *,
    top_n: int = 1,
    min_score: float | None = None,
    dry_run: bool = True,
    source: str = DEFAULT_SOURCE,
    capital: float | None = None,
) -> list[TradeIntent]:
    """Return BUY TradeIntents for selected ETFs or an empty list if none pass."""

    decision = select_top_etfs(list(candidates or []), top_n=top_n, min_score=min_score)
    intents: list[TradeIntent] = []
    for candidate in decision.selected:
        target_percent = _cap_target_percent(candidate.target_percent)
        intents.append(
            TradeIntent(
                symbol=candidate.symbol,
                side="BUY",
                quantity=_buy_quantity(candidate, target_percent, capital),
                target_percent=target_percent,
                reason=f"{decision.reason}; {candidate.symbol} score={candidate.score:.2f}",
                source=source,
                dry_run=dry_run,
            )
        )
    return intents
