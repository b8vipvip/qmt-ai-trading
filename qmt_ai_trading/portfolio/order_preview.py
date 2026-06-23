from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONSOLE_ROOT = Path("artifacts/reports/console")
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
    "live_trading_enabled": False,
    "allow_order_submit": False,
    "allow_order_cancel": False,
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default
    return default


def _write_json(path: Path, data: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path.as_posix()


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def _asset_from_account() -> dict[str, Any]:
    console = _read_json(CONSOLE_ROOT / "account_readonly" / "account_readonly_report.json", {})
    report = console.get("report") if isinstance(console, dict) else {}
    if not isinstance(report, dict):
        report = {}
    asset = report.get("asset") if isinstance(report.get("asset"), dict) else {}
    if asset:
        return asset
    runtime = _read_json(Path("local_runtime_account_stage91") / "account_asset_snapshot.json", {})
    return runtime.get("asset") if isinstance(runtime, dict) and isinstance(runtime.get("asset"), dict) else {}


def _positions_from_account() -> list[dict[str, Any]]:
    console = _read_json(CONSOLE_ROOT / "account_readonly" / "account_readonly_report.json", {})
    report = console.get("report") if isinstance(console, dict) else {}
    positions = report.get("positions") if isinstance(report, dict) else None
    if isinstance(positions, dict) and isinstance(positions.get("positions"), list):
        return [p for p in positions.get("positions", []) if isinstance(p, dict)]
    if isinstance(positions, list):
        return [p for p in positions if isinstance(p, dict)]
    runtime = _read_json(Path("local_runtime_account_stage91") / "account_positions_snapshot.json", {})
    positions = runtime.get("positions") if isinstance(runtime, dict) else []
    return [p for p in positions if isinstance(p, dict)] if isinstance(positions, list) else []


def _latest_market_rows() -> list[dict[str, Any]]:
    data = _read_json(CONSOLE_ROOT / "datahub" / "market_latest.json", {})
    rows = data.get("latest") if isinstance(data, dict) else []
    return [r for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def _latest_price(symbol: str) -> float:
    rows = _latest_market_rows()
    matched = [r for r in rows if str(r.get("symbol")) == symbol]
    if not matched:
        matched = rows
    if not matched:
        return 0.0
    row = matched[-1]
    return _float(row.get("close") or row.get("last_price") or row.get("price") or row.get("open"), 0.0)


def _latest_trade_intents() -> list[dict[str, Any]]:
    data = _read_json(CONSOLE_ROOT / "strategy" / "trade_intents.json", {})
    intents = data.get("trade_intents") if isinstance(data, dict) else []
    return [i for i in intents if isinstance(i, dict)] if isinstance(intents, list) else []


def _latest_risk_decisions() -> list[dict[str, Any]]:
    data = _read_json(CONSOLE_ROOT / "risk" / "risk_decisions.json", {})
    decisions = data.get("decisions") if isinstance(data, dict) else []
    return [d for d in decisions if isinstance(d, dict)] if isinstance(decisions, list) else []


def _decision_for_intent(intent: dict[str, Any], decisions: list[dict[str, Any]]) -> dict[str, Any]:
    intent_id = str(intent.get("intent_id") or intent.get("id") or "")
    symbol = str(intent.get("symbol") or "")
    for d in decisions:
        if intent_id and str(d.get("intent_id") or d.get("id") or "") == intent_id:
            return d
    for d in decisions:
        if symbol and str(d.get("symbol") or "") == symbol:
            return d
    return {}


def _asset_number(asset: dict[str, Any], *names: str) -> float:
    for name in names:
        if name in asset:
            return _float(asset.get(name), 0.0)
    return 0.0


def _position_qty(symbol: str, positions: list[dict[str, Any]]) -> int:
    for p in positions:
        ps = str(p.get("symbol") or p.get("stock_code") or p.get("m_strInstrumentID") or p.get("instrument_id") or "")
        if ps == symbol:
            return _int(p.get("quantity") or p.get("volume") or p.get("m_nVolume") or p.get("enable_amount"), 0)
    return 0


def build_order_preview(repo_root: str | Path = ".", output_dir: str | Path = "local_console_order_preview", params: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    params = params or {}
    max_single_order_amount = _float(params.get("max_single_order_amount"), 1000.0)
    min_lot = max(100, _int(params.get("min_lot"), 100))
    lot_size = max(100, _int(params.get("lot_size"), 100))

    asset = _asset_from_account()
    positions = _positions_from_account()
    intents = _latest_trade_intents()
    decisions = _latest_risk_decisions()
    cash = _asset_number(asset, "cash", "m_dCash", "available_cash", "enable_balance")
    total_asset = _asset_number(asset, "total_asset", "m_dTotalAsset", "asset", "total_balance") or cash
    market_value = _asset_number(asset, "market_value", "m_dMarketValue", "stock_market_value")

    previews: list[dict[str, Any]] = []
    blockers: list[str] = []
    for idx, intent in enumerate(intents, start=1):
        symbol = str(intent.get("symbol") or "")
        side = str(intent.get("side") or intent.get("action") or "HOLD").upper()
        decision = _decision_for_intent(intent, decisions)
        risk_decision = str(decision.get("decision") or "NO_RISK_DECISION")
        latest_price = _latest_price(symbol)
        target_weight = _float(intent.get("target_weight") or intent.get("target_percent"), 0.0)
        current_qty = _position_qty(symbol, positions)
        status = "PREVIEW_ONLY"
        preview_quantity = 0
        estimated_amount = 0.0
        reasons = ["真实订单预览只计算，不提交订单", "实盘总开关关闭，order_submit_enabled=false"]
        risk_flags: list[str] = []

        if risk_decision != "PASS_DRY_RUN":
            status = "BLOCKED_BY_RISK"
            risk_flags.append("risk_gate_not_passed")
        elif side not in {"BUY", "SELL"}:
            status = "NO_TRADE_SIGNAL"
            reasons.append(f"策略信号为 {side}，不生成买卖预览单")
        elif latest_price <= 0:
            status = "BLOCKED_NO_PRICE"
            risk_flags.append("latest_price_missing")
        elif side == "BUY":
            preview_quantity = max(min_lot, lot_size)
            estimated_amount = round(preview_quantity * latest_price, 2)
            if estimated_amount > cash:
                status = "BLOCKED_INSUFFICIENT_CASH"
                risk_flags.append("insufficient_cash")
            elif estimated_amount > max_single_order_amount:
                status = "BLOCKED_SINGLE_ORDER_LIMIT"
                risk_flags.append("single_order_amount_limit")
            else:
                status = "PREVIEW_BUY_READY_NOT_SUBMITTED"
                reasons.append("满足最小 100 股预览条件，但仍然不发单")
        elif side == "SELL":
            preview_quantity = max(lot_size, min_lot)
            if current_qty < preview_quantity:
                preview_quantity = current_qty - current_qty % lot_size
            estimated_amount = round(preview_quantity * latest_price, 2)
            if preview_quantity <= 0:
                status = "BLOCKED_NO_POSITION_TO_SELL"
                risk_flags.append("no_sellable_position")
            else:
                status = "PREVIEW_SELL_READY_NOT_SUBMITTED"
                reasons.append("满足卖出预览条件，但仍然不发单")

        if status.startswith("BLOCKED"):
            blockers.append(f"{symbol}:{status}")

        previews.append({
            "preview_id": f"preview-{idx:03d}-{symbol or 'NA'}",
            "intent_id": intent.get("intent_id") or intent.get("id") or f"intent-{idx}",
            "symbol": symbol,
            "side": side,
            "risk_decision": risk_decision,
            "latest_price": latest_price,
            "target_weight": target_weight,
            "current_quantity": current_qty,
            "preview_quantity": preview_quantity,
            "estimated_amount": estimated_amount,
            "cash_available": cash,
            "total_asset": total_asset,
            "max_single_order_amount": max_single_order_amount,
            "status": status,
            "preview_only": True,
            "can_submit_order": False,
            "requires_manual_confirmation": True,
            "reasons": reasons,
            "risk_flags": risk_flags,
            **SAFETY,
        })

    portfolio_status = "READY_EMPTY" if not previews else ("BLOCKED" if blockers else "PREVIEW_READY")
    summary = {
        "status": portfolio_status,
        "preview_count": len(previews),
        "blocked_count": len(blockers),
        "cash": cash,
        "total_asset": total_asset,
        "market_value": market_value,
        "position_count": len(positions),
        "trade_intent_count": len(intents),
        "risk_decision_count": len(decisions),
        "max_single_order_amount": max_single_order_amount,
        "min_lot": min_lot,
        "preview_only": True,
        "can_submit_order": False,
        "generated_at": _now(),
        **SAFETY,
    }
    preview_doc = {"status": portfolio_status, "previews": previews, **SAFETY}
    budget_doc = {"status": portfolio_status, "budget": summary, **SAFETY}
    report = {"status": portfolio_status, "summary": summary, "previews": previews, "blockers": blockers, "asset": asset, "positions": positions, **SAFETY}
    out_dir = root / output_dir
    console_dir = root / CONSOLE_ROOT / "portfolio"
    written = [
        _write_json(out_dir / "order_preview_summary.json", summary),
        _write_json(out_dir / "order_preview_latest.json", preview_doc),
        _write_json(out_dir / "portfolio_budget.json", budget_doc),
        _write_json(out_dir / "order_preview_report.json", report),
        _write_json(console_dir / "order_preview_latest.json", preview_doc),
        _write_json(console_dir / "portfolio_budget.json", budget_doc),
        _write_json(console_dir / "portfolio_status.json", summary),
    ]
    report.update({"output_dir": str(output_dir), "output_artifacts": written, "task_id": "order_preview_dry_run"})
    return report
