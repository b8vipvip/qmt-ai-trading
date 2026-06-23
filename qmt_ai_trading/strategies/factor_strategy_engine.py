from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SOURCE = "unified_factor_strategy"


def _flags(candidate: dict[str, Any]) -> list[str]:
    flags = list(candidate.get("risk_flags") or [])
    for required in ["not_live_trading", "no_order_submitted"]:
        if required not in flags:
            flags.append(required)
    return flags


def _safe_score(candidate: dict[str, Any]) -> float:
    try:
        return float(candidate.get("score", candidate.get("composite_score", 0)) or 0)
    except Exception:
        return 0.0


def candidates_to_signals(candidates: list[dict[str, Any]], max_positions: int = 3) -> list[dict[str, Any]]:
    ordered = sorted(candidates or [], key=lambda c: (int(c.get("rank") or 999999), -_safe_score(c)))
    signals: list[dict[str, Any]] = []
    for c in ordered[: max(0, int(max_positions or 0))]:
        score = c.get("score", c.get("composite_score", 0))
        action = "BUY" if score is not None and _safe_score(c) > 0 else "HOLD"
        signal = "BUY_CANDIDATE_DRY_RUN" if action == "BUY" else "HOLD_DRY_RUN"
        signals.append({
            "symbol": c.get("symbol"),
            "rank": c.get("rank"),
            "score": score,
            "signal": signal,
            "action": action,
            "target_weight": round(1 / max(1, int(max_positions or 1)), 4) if action == "BUY" else 0,
            "source": SOURCE,
            "dry_run": True,
            "real_market_data": "real_xtdata_readonly" in _flags(c),
            "risk_flags": _flags(c),
            "reasons": list(c.get("reasons") or []) + ["统一因子策略 dry-run 信号，仅用于人工复核"],
        })
    return signals


def signals_to_trade_intents(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    intents = []
    for i, s in enumerate(signals, 1):
        intents.append({
            "intent_id": f"unified-{i:03d}-{s.get('symbol')}",
            "created_at": now,
            "symbol": s.get("symbol"),
            "side": "BUY" if s.get("action") == "BUY" else "HOLD",
            "quantity": 0,
            "target_weight": s.get("target_weight"),
            "order_type": "DRY_RUN_INTENT",
            "source": SOURCE,
            "dry_run": True,
            "real_market_data": bool(s.get("real_market_data")),
            "requires_risk_gate": True,
            "requires_human_approval": True,
            "auto_approve": False,
            "risk_flags": _flags(s),
            "reasons": list(s.get("reasons") or []),
            "blocked_from_live": True,
            "not_live_trading": True,
            "no_order_submitted": True,
        })
    return intents


def build_factor_strategy(candidates: list[dict[str, Any]], max_positions: int = 3) -> dict[str, Any]:
    signals = candidates_to_signals(candidates, max_positions)
    intents = signals_to_trade_intents(signals)
    return {"strategy_signals": signals, "trade_intents": intents, "source": SOURCE, "dry_run": True, "no_order_submitted": True}
