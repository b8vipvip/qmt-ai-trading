from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ETF_WHITELIST_PREFIXES = ("510", "511", "512", "513", "515", "516", "517", "518", "560", "561", "562", "563", "588", "159")


def _flags(intent: dict[str, Any]) -> set[str]:
    return set(intent.get("risk_flags") or [])


def _is_etf_like(symbol: str) -> bool:
    code = (symbol or "").split(".")[0]
    return any(code.startswith(prefix) for prefix in ETF_WHITELIST_PREFIXES)


def _quantity(intent: dict[str, Any]) -> int:
    try:
        return int(float(intent.get("quantity") or 0))
    except Exception:
        return 0


def _target_weight(intent: dict[str, Any]) -> float:
    try:
        return float(intent.get("target_weight") or intent.get("target_percent") or 0)
    except Exception:
        return 0.0


def review_trade_intents(intents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    decisions = []
    for intent in intents or []:
        symbol = str(intent.get("symbol") or "")
        flags = _flags(intent)
        reasons: list[str] = []
        blockers: list[str] = []
        warnings: list[str] = []
        qty = _quantity(intent)
        weight = _target_weight(intent)

        if not intent.get("dry_run"):
            blockers.append("TradeIntent 未标记 dry_run=True")
        if intent.get("auto_approve"):
            blockers.append("auto_approve 必须为 false")
        if not intent.get("requires_risk_gate", True):
            blockers.append("TradeIntent 未要求 Risk Gate")
        if not intent.get("requires_human_approval", True):
            blockers.append("TradeIntent 未要求人工审批")
        if not intent.get("not_live_trading", True):
            blockers.append("not_live_trading 必须为 true")
        if intent.get("side") not in {"BUY", "SELL", "HOLD"}:
            blockers.append("side 必须为 BUY/SELL/HOLD")
        if not symbol:
            blockers.append("symbol 为空")
        elif not _is_etf_like(symbol):
            blockers.append("当前灰度前只允许 ETF 白名单前缀")
        if qty < 0:
            blockers.append("quantity 不能为负数")
        if qty and qty % 100 != 0:
            blockers.append("A 股/ETF 数量必须为 100 整数倍")
        if weight < 0:
            blockers.append("target_weight 不能为负数")
        if weight > 0.3334:
            warnings.append("target_weight 超过 33%，仅允许 dry-run 展示，实盘前需更严格仓位限制")
        if "real_xtdata_readonly" not in flags and not intent.get("real_market_data"):
            warnings.append("未检测到 real_xtdata_readonly 标记，按非真实行情候选处理")

        reasons.extend(blockers or ["dry-run TradeIntent 字段通过基础格式检查"])
        reasons.append("实盘总开关关闭，当前只输出风控审查结果")
        reasons.append("未进行人工二次确认，禁止进入实盘下单")
        reasons.extend(warnings)

        decision = "PASS_DRY_RUN" if not blockers else "REJECTED_DRY_RUN"
        decisions.append({
            "intent_id": intent.get("intent_id"),
            "symbol": symbol,
            "side": intent.get("side"),
            "quantity": qty,
            "target_weight": weight,
            "decision": decision,
            "approved": False,
            "dry_run": True,
            "risk_gate": "unified_risk_gate_dry_run",
            "real_market_data": bool(intent.get("real_market_data") or "real_xtdata_readonly" in flags),
            "blockers": blockers,
            "warnings": warnings,
            "reasons": reasons,
            "risk_flags": sorted(flags | {"not_live_trading", "no_order_submitted", "requires_human_approval"}),
            "no_order_submitted": True,
            "no_account_query": True,
            "no_qmt_trader_api": True,
            "auto_approve": False,
            "live_trading_enabled": False,
            "reviewed_at": now,
        })
    return decisions
