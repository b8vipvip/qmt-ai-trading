from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CONSOLE_ROOT = Path("artifacts/reports/console")

SAFETY_FLAGS = {
    "read_only": True,
    "dry_run": True,
    "live_disabled": True,
    "not_live_trading": True,
    "no_order_submitted": True,
    "no_account_query": True,
    "no_xttrader": True,
    "requires_human_approval": True,
    "approval_enabled": False,
    "approve_in_console": False,
    "auto_approve": False,
    "real_order_submitted": False,
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _expires(hours: int = 4) -> str:
    return (datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=hours)).isoformat()


def _read(module: str, filename: str, default: Any) -> Any:
    path = CONSOLE_ROOT / module / filename
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _by_id(rows: list[dict[str, Any]], key: str = "intent_id") -> dict[str, dict[str, Any]]:
    return {str(row.get(key)): row for row in rows if isinstance(row, dict) and row.get(key)}


def _request_status(order: dict[str, Any], decision: dict[str, Any]) -> str:
    if decision.get("decision") != "PASS_DRY_RUN":
        return "REJECTED_BY_RISK_DRY_RUN"
    if order.get("status") in {"PAPER_ACCEPTED_NO_FILL_QUANTITY_ZERO", "PAPER_ACCEPTED_DRY_RUN"}:
        return "PENDING_REVIEW_ONLY"
    return "BLOCKED_FOR_REVIEW"


def _approval_request(order: dict[str, Any], decision: dict[str, Any], position: dict[str, Any] | None) -> dict[str, Any]:
    intent_id = order.get("intent_id") or decision.get("intent_id") or order.get("order_id") or "unknown"
    symbol = order.get("symbol") or decision.get("symbol")
    status = _request_status(order, decision)
    reasons = []
    reasons.extend(_as_list(decision.get("reasons")))
    if order.get("reason"):
        reasons.append(order.get("reason"))
    if not reasons:
        reasons.append("Paper / Shadow dry-run 已生成，等待人工复核")
    return {
        "approval_id": f"approval-{intent_id}",
        "intent_id": intent_id,
        "paper_order_id": order.get("order_id"),
        "symbol": symbol,
        "side": order.get("side") or decision.get("side"),
        "quantity": int(float(order.get("quantity") or 0)),
        "target_weight": float(order.get("target_weight") or 0),
        "risk_decision": decision.get("decision", "MISSING_RISK_DECISION"),
        "paper_status": order.get("status"),
        "shadow_status": (position or {}).get("status"),
        "approval_status": status,
        "can_approve_live": False,
        "review_only": True,
        "residual_risk_accepted": False,
        "operator_confirmed": False,
        "created_at": _now(),
        "expires_at": _expires(),
        "summary": f"{symbol} {order.get('side')} dry-run 复核卡；当前仅人工查看，不允许控制台放行实盘。",
        "reasons": reasons,
        "required_checks": [
            "确认真实行情来源与时间戳",
            "确认 Risk Gate 为 PASS_DRY_RUN 且未绕过风控",
            "确认 Paper / Shadow 仅为模拟产物",
            "确认 quantity=0 时不得进入任何真实下单链路",
            "确认实盘总开关仍为关闭",
        ],
        **SAFETY_FLAGS,
    }


def build_human_approval_review(repo_root: str = ".", output_dir: str = "local_console_approval") -> dict[str, Any]:
    root = Path(repo_root)
    out = root / output_dir
    out.mkdir(parents=True, exist_ok=True)

    risk = _read("risk", "risk_decisions.json", {"decisions": []})
    paper_orders = _read("paper", "paper_orders.json", {"orders": []})
    positions = _read("paper", "shadow_positions.json", {"positions": []})
    pnl = _read("paper", "shadow_pnl.json", {"pnl": {}})

    decisions = [row for row in _as_list(risk.get("decisions") if isinstance(risk, dict) else []) if isinstance(row, dict)]
    orders = [row for row in _as_list(paper_orders.get("orders") if isinstance(paper_orders, dict) else []) if isinstance(row, dict)]
    pos_by_symbol = {str(row.get("symbol")): row for row in _as_list(positions.get("positions") if isinstance(positions, dict) else []) if isinstance(row, dict) and row.get("symbol")}
    decision_by_intent = _by_id(decisions)

    requests = []
    for order in orders:
        decision = decision_by_intent.get(str(order.get("intent_id")), {"decision": "MISSING_RISK_DECISION", "reasons": ["缺少 Risk Gate 决策"], **SAFETY_FLAGS})
        requests.append(_approval_request(order, decision, pos_by_symbol.get(str(order.get("symbol")))))

    status = {
        "status": "MANUAL_REVIEW_ONLY",
        "request_count": len(requests),
        "pending_count": sum(1 for item in requests if item.get("approval_status") == "PENDING_REVIEW_ONLY"),
        "approval_enabled": False,
        "approve_in_console": False,
        "message": "控制台只生成审批卡，不提供实盘批准按钮。进入真实下单前必须另走独立人工确认与实盘开关流程。",
        "source": "artifacts/reports/console/paper/paper_orders.json",
        "generated_at": _now(),
        **SAFETY_FLAGS,
    }
    report = {
        "status": "SUCCESS",
        "approval_status": status,
        "approval_requests": requests,
        "risk_decision_count": len(decisions),
        "paper_order_count": len(orders),
        "shadow_position_count": len(pos_by_symbol),
        "pnl": pnl.get("pnl", {}) if isinstance(pnl, dict) else {},
        "output_dir": out.as_posix(),
        **SAFETY_FLAGS,
    }

    (out / "approval_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "approval_requests.json").write_text(json.dumps({"requests": requests, **SAFETY_FLAGS}, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "approval_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
