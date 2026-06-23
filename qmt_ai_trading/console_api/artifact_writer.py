from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAFETY = {
    "read_only": True,
    "dry_run": True,
    "live_disabled": True,
    "no_order_submitted": True,
    "requires_human_approval": True,
    "account_masked": True,
    "order_submit_enabled": False,
    "order_cancel_enabled": False,
    "real_order_submitted": False,
    "allow_order_submit": False,
    "allow_order_cancel": False,
    "live_trading_enabled": False,
}

CONSOLE_ROOT = Path("artifacts/reports/console")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _with_safety(task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    out = {**SAFETY, **payload}
    out.setdefault("status", "READY")
    out["task_id"] = task_id
    out["updated_at"] = _now()
    return _json_safe(out)


def _write(module: str, filename: str, task_id: str, payload: dict[str, Any]) -> str:
    path = CONSOLE_ROOT / module / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_with_safety(task_id, payload), ensure_ascii=False, indent=2), encoding="utf-8")
    return path.as_posix()


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def _first_not_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _load_xtdata_live_details(output: dict[str, Any]) -> dict[str, Any]:
    root = Path(str(output.get("output_dir") or "local_console_xtdata_live_stage87"))
    return {
        "status": _read_json(root / "xtdata_live_status.json", {}) or {},
        "snapshots": _read_json(root / "xtdata_live_snapshots.json", {}) or {},
        "bars": _read_json(root / "xtdata_live_bars.json", {}) or {},
    }


def _market_rows_from_xtdata(output: dict[str, Any]) -> list[dict[str, Any]]:
    details = _load_xtdata_live_details(output)
    bars_payload = details.get("bars") or {}
    rows = _as_list(bars_payload.get("bars") if isinstance(bars_payload, dict) else bars_payload)
    symbol = output.get("symbol") or (bars_payload.get("symbol") if isinstance(bars_payload, dict) else None) or "510300.SH"
    period = output.get("period") or (bars_payload.get("period") if isinstance(bars_payload, dict) else None) or "1d"
    source = output.get("provider") or "xtdata_live_readonly"
    real_market_data = bool(output.get("real_market_data") or (isinstance(bars_payload, dict) and bars_payload.get("real_market_data")))
    sandbox_fallback = bool(output.get("sandbox_fallback", False))
    normalized: list[dict[str, Any]] = []
    for row in rows[-20:]:
        if not isinstance(row, dict):
            continue
        item = {
            "symbol": row.get("symbol", symbol),
            "period": period,
            "time": _first_not_none(row.get("time"), row.get("datetime"), row.get("timestamp"), row.get("stime"), row.get("index")),
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "volume": _first_not_none(row.get("volume"), row.get("vol")),
            "amount": row.get("amount"),
            "source": source,
            "real_market_data": real_market_data,
            "sandbox_fallback": sandbox_fallback,
        }
        if item["open"] is None and item["close"] is None and "value" in row:
            item["value"] = row.get("value")
        normalized.append(item)
    if normalized:
        return normalized
    snapshots_payload = details.get("snapshots") or {}
    for row in _as_list(snapshots_payload.get("snapshots") if isinstance(snapshots_payload, dict) else snapshots_payload):
        if isinstance(row, dict):
            normalized.append({
                "symbol": row.get("symbol", symbol),
                "period": period,
                "time": _first_not_none(row.get("time"), row.get("datetime"), row.get("timestamp")),
                "open": row.get("open"),
                "high": row.get("high"),
                "low": row.get("low"),
                "close": _first_not_none(row.get("lastPrice"), row.get("last_price"), row.get("price"), row.get("close")),
                "volume": _first_not_none(row.get("volume"), row.get("vol")),
                "amount": row.get("amount"),
                "source": source,
                "real_market_data": real_market_data,
                "sandbox_fallback": sandbox_fallback,
            })
    return normalized


def _candidates(output: dict[str, Any]) -> list[Any]:
    return _as_list(output.get("factor_candidates") or output.get("candidates"))


def _signals(output: dict[str, Any]) -> list[Any]:
    return _as_list(output.get("strategy_signals") or output.get("signals"))


def _trade_intents(output: dict[str, Any]) -> list[Any]:
    return _as_list(output.get("trade_intents") or output.get("trade_intent"))


def _risk_decisions(output: dict[str, Any]) -> list[Any]:
    return _as_list(output.get("risk_decisions") or output.get("decisions"))


def write_task_output_to_console_artifacts(task_id: str, output: dict[str, Any]) -> list[str]:
    if not isinstance(output, dict):
        output = {"value": output}
    written: list[str] = []

    def w(module: str, filename: str, payload: dict[str, Any]) -> None:
        written.append(_write(module, filename, task_id, payload))

    if task_id in {"data_cache_check", "qmt_data_diagnostics_readonly"}:
        w("datahub", "datahub_status.json", {"module": "Data Hub", "status": "READY", "report": output})
        w("datahub", "datahub_real_cache.json", {"status": "READY", "cache": output})

    if task_id in {"market_snapshot_readonly", "xtdata_live_readonly_smoke", "market_replay_sandbox"}:
        if task_id == "xtdata_live_readonly_smoke":
            market_rows = _market_rows_from_xtdata(output)
            symbols = sorted({str(row.get("symbol")) for row in market_rows if row.get("symbol")}) or _as_list(output.get("symbols")) or ["510300.SH"]
            sample = {"symbol": symbols[0], "period": output.get("period", "1d"), "source": output.get("provider", "xtdata_live_readonly"), "real_market_data": bool(output.get("real_market_data", False)), "sandbox_fallback": bool(output.get("sandbox_fallback", True)), "rows": market_rows}
            w("market", "xtdata_live_status.json", {"status": "READY", "real_market_data": sample["real_market_data"], "sandbox_fallback": sample["sandbox_fallback"], "sample": sample, "rows": market_rows, "report": output})
            w("datahub", "market_latest.json", {"status": "READY", "latest": market_rows or [sample], "source": sample["source"], "real_market_data": sample["real_market_data"], "sandbox_fallback": sample["sandbox_fallback"]})
            w("datahub", "datahub_symbols.json", {"status": "READY", "symbols": symbols})
            w("datahub", "datahub_real_cache.json", {"status": "READY", "rows": market_rows, "source": sample["source"], "real_market_data": sample["real_market_data"]})
            w("datahub", "datahub_status.json", {"module": "Data Hub", "status": "READY", "last_market_task": task_id, "real_market_data": sample["real_market_data"], "sandbox_fallback": sample["sandbox_fallback"]})
        else:
            market = output.get("market") or output.get("ohlcv") or output
            sample = {"symbol": output.get("symbol", "510300.SH"), "period": output.get("period", output.get("timeframe", "1d")), "source": output.get("source", output.get("provider", "readonly/mock")), "market": market}
            w("market", "xtdata_live_status.json", {"status": "READY", "real_market_data": bool(output.get("real_market_data", False)), "sample": sample})
            w("datahub", "market_latest.json", {"status": "READY", "latest": [sample]})
            w("datahub", "datahub_symbols.json", {"status": "READY", "symbols": [sample["symbol"]]})
            w("datahub", "datahub_status.json", {"module": "Data Hub", "status": "READY", "last_market_task": task_id})

    if task_id in {"factor_scan", "factor_research_dry_run", "research_score_etf", "etf_rotation_candidates"} or _candidates(output):
        candidates = _candidates(output)
        w("research", "factor_context.json", {"status": "READY", "source_task": task_id, "candidate_count": len(candidates), "context": output.get("context", {})})
        w("research", "factor_candidates.json", {"status": "READY", "candidates": candidates})
        w("research", "factor_values.json", {"status": "READY", "factors": output.get("factors", candidates)})

    if task_id in {"strategy_dry_run_signals", "factor_strategy_dry_run", "daily_pipeline_dry_run", "etf_rotation_candidates"} or _signals(output) or _trade_intents(output):
        signals = _signals(output)
        intents = _trade_intents(output)
        if not intents and signals:
            intents = [{"symbol": s.get("symbol", "510300.SH") if isinstance(s, dict) else "510300.SH", "side": "HOLD", "dry_run": True, "source": task_id, "reason": "derived from dry-run signal"} for s in signals]
        w("strategy", "strategy_signals.json", {"status": "READY", "signals": signals})
        w("strategy", "trade_intents.json", {"status": "READY", "trade_intents": intents})

    if task_id in {"risk_gate_dry_run", "risk_gate_dry_run_check", "factor_strategy_dry_run", "live_readiness_blockers_review"} or _risk_decisions(output):
        decisions = _risk_decisions(output)
        w("risk", "risk_decisions.json", {"status": "READY", "decisions": decisions})
        w("risk", "risk_report.json", {"status": "READY", "blocked_by_risk": output.get("blocked_by_risk", True), "decision_count": len(decisions), "report": output})

    if task_id.startswith("agent_"):
        w("agent", "agent_context.json", {"status": "READY", "source_task": task_id})
        w("agent", "agent_research_report.json", {"status": "READY", "report": output})

    if "backtest" in task_id or "replay" in task_id:
        w("backtest", "shadow_replay_result.json", {"status": "READY", "shadow_replay": output})

    if task_id == "paper_trading_dry_run":
        orders = _as_list(output.get("orders"))
        if not orders and output.get("paper_order_count", 0):
            orders = [{"order_id": "paper-dry-run-1", "symbol": "510300.SH", "side": "HOLD", "status": "SIMULATED", "dry_run": True}]
        positions = _as_list(output.get("positions"))
        if not positions and output.get("shadow_position_count", 0):
            positions = [{"symbol": "510300.SH", "quantity": 0, "market_value": 0, "dry_run": True}]
        pnl = output.get("pnl") or {"realized": 0, "unrealized": 0, "total": 0, "dry_run": True}
        w("paper", "paper_trading_report.json", {"status": "READY", "report": output})
        w("paper", "paper_orders.json", {"status": "READY", "orders": orders})
        w("paper", "shadow_positions.json", {"status": "READY", "positions": positions})
        w("paper", "shadow_pnl.json", {"status": "READY", "pnl": pnl})

    if task_id == "human_approval_review_dry_run":
        approval_status = output.get("approval_status") or {"status": "MANUAL_REVIEW_ONLY", "approval_enabled": False, "approve_in_console": False}
        approval_requests = _as_list(output.get("approval_requests"))
        w("approval", "approval_status.json", {"status": approval_status.get("status", "MANUAL_REVIEW_ONLY"), "approval": approval_status})
        w("approval", "approval_requests.json", {"status": "READY", "requests": approval_requests})

    if task_id == "monitoring_alert_dry_run":
        w("monitoring", "monitoring_input_context.json", {"status": "READY", "context": output})
        w("monitoring", "monitoring_alerts.json", {"status": "READY", "alerts": _as_list(output.get("alerts"))})
        w("monitoring", "circuit_breaker_status.json", {"status": output.get("circuit_breaker_status", "READY"), "report": output})

    if task_id == "account_readonly_dry_run":
        w("account_readonly", "account_readonly_report.json", {"status": output.get("status", "READY"), "account_id": output.get("account_id", "***MASKED***"), "report": output})

    if task_id == "workflow_dry_run_check":
        w("workflow", "workflow_status.json", {"status": "READY", "workflow": output})

    if written:
        w("workflow", "last_task_output.json", {"status": "READY", "last_task_id": task_id, "written_artifacts": written})
    return written
