from __future__ import annotations

import json
from collections.abc import Iterable

from .models import FinalAuthorizationEvidence, FinalAuthorizationPackage

MOJIBAKE_MARKERS = ("鏂", "闃", "鈥")


def _value(value: object) -> str:
    return str(getattr(value, "value", value))


def _lines(items: Iterable[str], *, empty: str = "None", prefix: str = "- ") -> list[str]:
    values = [str(item) for item in items if str(item)]
    if not values:
        values = [empty]
    return [f"{prefix}{item}" for item in values]


def _assert_utf8_markdown_text(text: str) -> None:
    """Fail fast if known mojibake markers appear in generated Markdown."""

    found = [marker for marker in MOJIBAKE_MARKERS if marker in text]
    if found:
        raise ValueError(f"Final authorization Markdown contains mojibake markers: {', '.join(found)}")


def format_final_authorization_evidence(evidence: FinalAuthorizationEvidence) -> str:
    """Format one final-authorization evidence row for the Markdown table."""

    return (
        f"| {_value(evidence.evidence_type)} | {_value(evidence.status)} | "
        f"{evidence.severity} | {evidence.source_path} | {evidence.summary} | "
        f"{evidence.blocked_reason} |"
    )


def format_final_authorization_package_json(package: FinalAuthorizationPackage) -> str:
    """Serialize a package with UTF-8 Chinese preserved instead of escaped."""

    return json.dumps(package.to_dict(), ensure_ascii=False, indent=2)


def format_final_authorization_package_markdown(package: FinalAuthorizationPackage) -> str:
    """Build the review-only final authorization Markdown package."""

    data = package.to_dict()
    lines = [
        "# Final manual authorization package summary",
        "",
        f"Package ID: `{data['package_id']}`",
        f"Created at: `{data['created_at']}`",
        "",
        "## Decision",
        f"- Decision: **{data['decision']}**",
        "- READY_FOR_FINAL_SIGNOFF_REVIEW means ready for human final signoff review only; it is not live trading authorization.",
        "",
        "## Required evidence",
        "- Live Env Check / Live Manual Prep / Gray Decision Package / Gray Rehearsal / Live Gray Readiness / Live Readiness Audit / Risk Gate / Human Approval / Paper Trading / Monitoring / Data Quality / Agent Research / Notification Dry Run / Dashboard / Final Acceptance",
        "",
        "## Evidence table",
        "| Type | Status | Severity | Source | Summary | Blocked reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(format_final_authorization_evidence(evidence) for evidence in package.evidence)
    lines.extend(["", "## Blocked reasons", *_lines(data["blocked_reasons"])])
    lines.extend(["", "## Warnings", *_lines(data["warnings"])])
    lines.extend(["", "## Manual checklist", *_lines(data["checklist"], prefix="- [ ] ")])
    lines.extend(["", "## Forbidden items", *_lines(data["forbidden_items"])])
    lines.extend(["", "## Residual risks", *_lines(data["residual_risks"])])
    lines.extend(["", "## Future stage requirements", *_lines(data["future_stage_requirements"])])
    lines.extend(["", "## Signoff placeholders", *_lines(data["signoff_placeholders"])])
    lines.extend(
        [
            "",
            "## Safety note",
            data["safety_note"],
            "",
            "## Next separate stage",
            "阶段四十：实盘开关隔离与最终红线复核（仍默认关闭）。",
            "阶段四十仍不执行实盘，不下单、不调用 xttrader、不真实发送通知、不查询账户资金持仓订单成交。",
        ]
    )
    markdown = "\n".join(lines) + "\n"
    _assert_utf8_markdown_text(markdown)
    return markdown
