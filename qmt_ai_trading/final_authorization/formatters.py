from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

BAD_MOJIBAKE = ("鏂", "闃", "鈥", "€?")


def _value(v: Any) -> Any:
    if isinstance(v, Enum):
        return v.value
    return v


def _safe_text(v: Any) -> str:
    text = "" if v is None else str(_value(v))
    for bad in BAD_MOJIBAKE:
        if bad in text:
            return ""
    return text


def _to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return obj
    return dict(getattr(obj, "__dict__", {}))


def _dedupe(items: list[Any]) -> list[str]:
    out = []
    seen = set()
    for item in items or []:
        s = _safe_text(item)
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _future_stage_requirements() -> list[str]:
    return [
        "新阶段必须单独人工确认。",
        "新阶段仍默认关闭实盘。",
        "必须再次确认 QMT 环境。",
        "必须再次确认 Risk Gate。",
        "必须再次确认 Human Approval。",
        "必须再次确认 Paper Trading。",
        "必须再次确认 Live Readiness Audit。",
        "必须再次确认 Monitoring / Circuit Breaker。",
        "必须再次确认 Notification 是否仍 dry-run。",
        "必须再次确认 allowed_symbols 和 capital limits。",
        "不得直接从本包自动执行交易。",
    ]


def format_final_authorization_evidence(evidence: Any) -> str:
    d = _to_dict(evidence)
    return (
        f"| {_safe_text(d.get('evidence_type'))} "
        f"| {_safe_text(d.get('status'))} "
        f"| {_safe_text(d.get('severity'))} "
        f"| {_safe_text(d.get('source_path'))} "
        f"| {_safe_text(d.get('summary'))} "
        f"| {_safe_text(d.get('blocked_reason'))} |"
    )


def format_final_authorization_package_markdown(package: Any) -> str:
    d = _to_dict(package)
    evidence = getattr(package, "evidence", d.get("evidence", [])) or []
    lines = [
        "# Final manual authorization package summary",
        "",
        f"Package ID: `{_safe_text(d.get('package_id'))}`",
        f"Created at: `{_safe_text(d.get('created_at'))}`",
        "",
        "## Decision",
        f"- Decision: **{_safe_text(d.get('decision'))}**",
        "- READY_FOR_FINAL_SIGNOFF_REVIEW means ready for human final signoff review only; it is not live trading authorization.",
        "",
        "## Required evidence",
        "- Live Env Check / Live Manual Prep / Gray Decision Package / Gray Rehearsal / Live Gray Readiness / Live Readiness Audit / Risk Gate / Human Approval / Paper Trading / Monitoring / Data Quality / Agent Research / Notification Dry Run / Dashboard / Final Acceptance",
        "",
        "## Evidence table",
        "| Type | Status | Severity | Source | Summary | Blocked reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in evidence:
        lines.append(format_final_authorization_evidence(item))
    sections = [
        ("Blocked reasons", _dedupe(d.get("blocked_reasons", []))),
        ("Warnings", _dedupe(d.get("warnings", []))),
        ("Manual checklist", _dedupe(d.get("checklist", []))),
        ("Forbidden items", _dedupe(d.get("forbidden_items", []))),
        ("Residual risks", _dedupe(d.get("residual_risks", []))),
        ("Future stage requirements", _future_stage_requirements()),
        ("Signoff placeholders", _dedupe(d.get("signoff_placeholders", []))),
    ]
    for title, items in sections:
        lines += ["", f"## {title}"]
        lines += [f"- {x}" for x in items] if items else ["- None"]
    lines += [
        "",
        "## Safety note",
        "Final authorization package is review-only and dry-run. It does not enable live trading, does not submit orders, does not send real notifications, and does not call xttrader or QMT trading APIs.",
        "",
        "## Next separate stage",
        "阶段四十：实盘开关隔离与最终红线复核（仍默认关闭）。",
        "",
    ]
    return "\n".join(line for line in lines if not any(bad in line for bad in BAD_MOJIBAKE))


def format_final_authorization_package_json(package: Any) -> str:
    return json.dumps(_to_dict(package), ensure_ascii=False, indent=2, default=str)
