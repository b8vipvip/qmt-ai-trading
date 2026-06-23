from __future__ import annotations

import json
from datetime import datetime, timedelta
from math import sqrt
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from qmt_ai_trading.datahub.etf_universe import get_default_etf_universe
from qmt_ai_trading.datahub.models import MarketBar
from .factor_config import build_default_config

CONSOLE_MARKET_LATEST = Path("artifacts/reports/console/datahub/market_latest.json")


def make_mock_bars(symbol: str, days: int = 90) -> list[MarketBar]:
    base = 2.5 + (abs(hash(symbol)) % 120) / 100
    bars = []
    for i in range(days):
        close = base * (1 + 0.0015 * i + 0.015 * ((i % 11) - 5) / 100)
        volume = 1000000 + (i % 17) * 25000 + (abs(hash(symbol)) % 1000)
        bars.append(MarketBar(symbol, (datetime.utcnow() - timedelta(days=days - i)).date().isoformat(), close * 0.99, close * 1.01, close * 0.98, close, volume, source="mock"))
    return bars


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _load_console_market_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        if not CONSOLE_MARKET_LATEST.exists():
            return [], {}
        data = json.loads(CONSOLE_MARKET_LATEST.read_text(encoding="utf-8"))
        rows = data.get("latest") if isinstance(data, dict) else []
        return [row for row in rows if isinstance(row, dict)], data if isinstance(data, dict) else {}
    except Exception as exc:
        return [], {"load_error": str(exc)}


def _rows_to_bars(rows: list[dict[str, Any]]) -> dict[str, list[MarketBar]]:
    grouped: dict[str, list[MarketBar]] = {}
    for row in rows:
        symbol = str(row.get("symbol") or "").strip()
        if not symbol:
            continue
        close = _float_or_none(row.get("close"))
        if close is None or close <= 0:
            continue
        bar = MarketBar(
            symbol=symbol,
            datetime=row.get("index") or row.get("time") or row.get("datetime"),
            open=_float_or_none(row.get("open")),
            high=_float_or_none(row.get("high")),
            low=_float_or_none(row.get("low")),
            close=close,
            volume=_float_or_none(row.get("volume")),
            amount=_float_or_none(row.get("amount")),
            source=str(row.get("source") or "console_datahub"),
        )
        grouped.setdefault(symbol, []).append(bar)
    return grouped


def load_real_datahub_bars() -> tuple[dict[str, list[MarketBar]], dict[str, Any]]:
    rows, meta = _load_console_market_rows()
    grouped = _rows_to_bars(rows)
    has_real = bool(meta.get("real_market_data")) or any(bool(row.get("real_market_data")) for row in rows)
    fallback = bool(meta.get("sandbox_fallback")) or any(bool(row.get("sandbox_fallback")) for row in rows)
    source = meta.get("source") or (rows[0].get("source") if rows else "")
    quality = "real_xtdata_readonly" if grouped and has_real and not fallback else "sample_offline"
    return grouped, {"row_count": len(rows), "symbol_count": len(grouped), "real_market_data": has_real, "sandbox_fallback": fallback, "source": source, "quality_level": quality}


def _closes(bars):
    return [float(b.close) for b in bars if b.close and b.close > 0]


def _vols(bars):
    return [float(b.volume) for b in bars if b.volume is not None]


def _ret(closes, w):
    return (closes[-1] / closes[-w - 1] - 1) if len(closes) >= w + 1 else None


def compute_factor_value(factor_id: str, bars: list[MarketBar], params: dict[str, Any] | None = None) -> float | None:
    params = params or {}
    c = _closes(bars)
    v = _vols(bars)
    if factor_id.startswith("momentum_"):
        return _ret(c, int(params.get("window", factor_id.split("_")[1][:-1])))
    if factor_id == "return_reversal_5d":
        x = _ret(c, int(params.get("window", 5)))
        return -x if x is not None else None
    if factor_id == "volatility_20d":
        w = int(params.get("window", 20))
        if len(c) < w + 1:
            return None
        rs = [c[i] / c[i - 1] - 1 for i in range(len(c) - w, len(c)) if c[i - 1] > 0]
        return pstdev(rs) * sqrt(252) if len(rs) > 1 else None
    if factor_id == "volume_ratio_20d":
        w = int(params.get("window", 20))
        return (v[-1] / mean(v[-w:])) if len(v) >= w and mean(v[-w:]) else None
    if factor_id == "drawdown_60d":
        w = int(params.get("window", 60))
        s = c[-w:] if len(c) >= w else []
        return min((x / max(s[: i + 1]) - 1 for i, x in enumerate(s)), default=None) if s else None
    if factor_id == "ma_trend_20_60":
        sw = int(params.get("short_window", 20))
        lw = int(params.get("long_window", 60))
        return mean(c[-sw:]) / mean(c[-lw:]) - 1 if len(c) >= lw else None
    return None


def _score_row(symbol: str, bars: list[MarketBar], factor_set: list[str], cfg: dict[str, Any], data_flags: list[str]) -> dict[str, Any]:
    vals = {fid: compute_factor_value(fid, bars, (cfg.get(fid).params if cfg.get(fid) else {})) for fid in factor_set}
    nums = [(v, cfg[f].weight, -1 if cfg[f].direction == "negative" else 1) for f, v in vals.items() if v is not None and f in cfg]
    score = sum(v * w * d for v, w, d in nums) / sum(abs(w) for _, w, _ in nums) if nums else None
    reasons = [f"{k}={v:.4f}" for k, v in vals.items() if v is not None][:3]
    if not reasons:
        reasons = ["真实行情数量不足，暂不产生有效因子值"]
    return {"symbol": symbol, "factor_values": vals, "composite_score": score, "rank": 0, "bar_count": len(bars), "data_source": bars[-1].source if bars else "", "reasons": reasons, "risk_flags": data_flags.copy()}


def run_factor_scan(params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = params or {}
    factor_set = params.get("factor_set") or [c.factor_id for c in build_default_config() if c.enabled]
    cfg = {c.factor_id: c for c in build_default_config()}
    real_bars, real_meta = load_real_datahub_bars()
    prefer_real = params.get("prefer_real_data", True) is not False
    rows = []

    if prefer_real and real_bars:
        for symbol, bars in sorted(real_bars.items()):
            flags = ["not_live_trading", "real_xtdata_readonly", "no_order_submitted"]
            if real_meta.get("sandbox_fallback"):
                flags.append("sandbox_fallback")
            rows.append(_score_row(symbol, bars, factor_set, cfg, flags))
        data_source = real_meta.get("source") or "console_datahub"
        quality_level = real_meta.get("quality_level") or "real_xtdata_readonly"
    else:
        for item in get_default_etf_universe():
            bars = make_mock_bars(item.symbol, 90)
            rows.append(_score_row(item.symbol, bars, factor_set, cfg, ["not_live_trading", "mock_data"]))
        data_source = "mock"
        quality_level = "sample_offline"

    rows = sorted(rows, key=lambda r: (r["composite_score"] is not None, r["composite_score"] or -999), reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    from .factor_evaluation import evaluate_factor_results
    from .candidate_builder import build_candidates
    from .factor_report import build_factor_report

    limit = int(params.get("limit", 5) or 5)
    evaluation = evaluate_factor_results(rows)
    candidates = build_candidates(rows, limit=limit)
    report = build_factor_report(rows, evaluation, candidates, params)
    return {
        "ok": True,
        "task_id": "factor_scan",
        "data_source": data_source,
        "quality_level": quality_level,
        "real_market_data": bool(real_meta.get("real_market_data")) if real_bars else False,
        "sandbox_fallback": bool(real_meta.get("sandbox_fallback")) if real_bars else True,
        "bar_source": "artifacts/reports/console/datahub/market_latest.json" if real_bars else "mock",
        "not_live_trading": True,
        "no_order_submitted": True,
        "factor_results": rows,
        "factor_evaluation": evaluation,
        "factor_candidates": candidates,
        "factor_report": report,
        "artifacts": ["factor_results.json", "factor_evaluation.json", "factor_candidates.json", "factor_report.json"],
    }
