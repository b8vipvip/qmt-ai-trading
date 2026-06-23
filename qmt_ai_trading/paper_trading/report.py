from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import SAFETY_FLAGS

INITIAL_CASH = 100000.0
CONSOLE_ROOT = Path("artifacts/reports/console")


def _dump(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _md(path: Path, title: str, data: Any) -> None:
    lines = [f"# {title}", "", "```json", json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), "```", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _read(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def _console(module: str, filename: str, default: Any) -> Any:
    return _read(CONSOLE_ROOT / module / filename, default)


def _latest_price(rows: list[dict[str, Any]], symbol: str) -> float:
    values = [row for row in rows if isinstance(row, dict) and row.get("symbol") == symbol]
    if not values:
        values = [row for row in rows if isinstance(row, dict)]
    for row in reversed(values):
        try:
            price = float(row.get("close") or row.get("price") or 0)
            if price > 0:
                return price
        except Exception:
            continue
    return 0.0


def _decision_allowed(decision: dict[str, Any]) -> bool:
    return str(decision.get("decision", "")).upper() == "PASS_DRY_RUN"


def _reason(decision: dict[str, Any]) -> str:
    reasons = decision.get("reasons") or decision.get("blockers") or decision.get("warnings") or []
    return "; ".join(str(x) for x in reasons) if reasons else "Risk Gate dry-run review completed"


def _order_status(intent: dict[str, Any], decision: dict[str, Any]) -> str:
    side = str(intent.get("side", "HOLD")).upper()
    if side == "HOLD":
        return "SKIPPED_HOLD"
    if not _decision_allowed(decision):
        return "PAPER_REJECTED_DRY_RUN"
    qty = int(float(intent.get("quantity") or 0))
    return "PAPER_ACCEPTED_NO_FILL_QUANTITY_ZERO" if qty == 0 else "PAPER_ACCEPTED_DRY_RUN"


def _paper_order(intent: dict[str, Any], decision: dict[str, Any], price: float) -> dict[str, Any]:
    qty = int(float(intent.get("quantity") or 0))
    status = _order_status(intent, decision)
    return {
        "order_id": f"paper-{intent.get('intent_id', intent.get('symbol', 'unknown'))}",
        "intent_id": intent.get("intent_id"),
        "symbol": intent.get("symbol"),
        "side": intent.get("side"),
        "quantity": qty,
        "target_weight": float(intent.get("target_weight") or intent.get("target_percent") or 0),
        "intent_price": float(intent.get("intent_price") or intent.get("price") or price or 0),
        "simulated_fill_price": price if qty else 0,
        "status": status,
        "fill_status": "NO_FILL_QUANTITY_ZERO" if qty == 0 else ("SIMULATED_FILL" if _decision_allowed(decision) else "REJECTED"),
        "risk_decision": decision.get("decision"),
        "risk_summary": "dry-run 通过" if _decision_allowed(decision) else "dry-run 拒绝",
        "reason": _reason(decision),
        "paper_order": True,
        "real_order_submitted": False,
        "source": "risk_decision_to_paper_shadow",
        **SAFETY_FLAGS,
    }


def _shadow_position(order: dict[str, Any], price: float) -> dict[str, Any]:
    qty = int(order.get("quantity") or 0)
    market_value = qty * price
    return {
        "symbol": order.get("symbol"),
        "quantity": qty,
        "average_price": price if qty else 0,
        "last_price": price,
        "target_weight": order.get("target_weight", 0),
        "position_value": market_value,
        "unrealized_pnl": 0,
        "status": "TARGET_ONLY_NO_LIVE_POSITION" if qty == 0 else "SHADOW_POSITION",
        "reason": "TradeIntent quantity=0，因此只记录影子目标，不模拟真实成交" if qty == 0 else "Paper fill simulated after Risk Gate dry-run pass",
        **SAFETY_FLAGS,
    }


def _run_from_console_artifacts(output_dir: Path) -> dict[str, Any]:
    strategy = _console("strategy", "trade_intents.json", {"trade_intents": []})
    risk = _console("risk", "risk_decisions.json", {"decisions": []})
    market = _console("datahub", "market_latest.json", {"latest": []})
    intents = strategy.get("trade_intents", []) if isinstance(strategy, dict) else []
    decisions = risk.get("decisions", []) if isinstance(risk, dict) else []
    rows = market.get("latest", []) if isinstance(market, dict) else []
    decision_by_id = {d.get("intent_id"): d for d in decisions if isinstance(d, dict)}

    orders: list[dict[str, Any]] = []
    positions: list[dict[str, Any]] = []
    for intent in intents:
        if not isinstance(intent, dict):
            continue
        decision = decision_by_id.get(intent.get("intent_id"), {"decision": "REJECTED_DRY_RUN", "reasons": ["缺少 Risk Gate 决策"], **SAFETY_FLAGS})
        if decision.get("decision") != "PASS_DRY_RUN":
            # 仍记录拒绝订单，方便前端追溯；不会生成影子持仓。
            price = _latest_price(rows, str(intent.get("symbol") or ""))
            orders.append(_paper_order(intent, decision, price))
            continue
        price = _latest_price(rows, str(intent.get("symbol") or ""))
        order = _paper_order(intent, decision, price)
        orders.append(order)
        positions.append(_shadow_position(order, price))

    pnl = {
        "initial_cash": INITIAL_CASH,
        "current_cash": INITIAL_CASH,
        "position_value": sum(float(p.get("position_value") or 0) for p in positions),
        "total_value": INITIAL_CASH + sum(float(p.get("position_value") or 0) for p in positions),
        "daily_pnl": 0,
        "cumulative_pnl": 0,
        "portfolio_return": 0,
        "max_drawdown": 0,
        "warnings": ["Paper Trading 仅消费 PASS_DRY_RUN，当前不提交任何真实订单"],
        **SAFETY_FLAGS,
    }
    report = {
        "status": "SUCCESS",
        "paper_order_count": len(orders),
        "paper_fill_count": sum(1 for o in orders if o.get("fill_status") == "SIMULATED_FILL"),
        "shadow_position_count": len(positions),
        "source": "artifacts/reports/console/risk/risk_decisions.json",
        "trade_intent_count": len(intents),
        "risk_decision_count": len(decisions),
        "paper_trading_status": "SAFE_PAPER_ONLY",
        "safety_status": "PASS",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "real_order_submitted": False,
        **SAFETY_FLAGS,
    }

    artifacts = {
        "paper_trading_report": report,
        "paper_orders": {"status": "READY", "orders": orders, "paper_order_summary": orders, **SAFETY_FLAGS},
        "shadow_positions": {"status": "READY", "positions": positions, "position_summary": positions, **SAFETY_FLAGS},
        "shadow_pnl": {"status": "READY", "pnl": pnl, "pnl_summary": pnl, **SAFETY_FLAGS},
        "paper_input_context": {"strategy": strategy, "risk": risk, "market": market, **SAFETY_FLAGS},
    }
    for name, data in artifacts.items():
        _dump(output_dir / f"{name}.json", data)
        _md(output_dir / f"{name}.md", name, data)

    return {**report, "output_dir": output_dir.as_posix(), "orders": orders, "positions": positions, "pnl": pnl}


def run_paper_trading_stage89(repo_root=".", input_stage=88, output_dir="local_console_paper_stage89", dry_run=True, read_only=True):
    root = Path(repo_root)
    out = root / output_dir
    out.mkdir(parents=True, exist_ok=True)
    return _run_from_console_artifacts(out)
