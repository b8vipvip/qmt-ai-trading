from __future__ import annotations

import json
from typing import Any

from .models import RedlineReviewReport, enum_value, to_plain


def format_redline_finding(finding: Any) -> str:
    d = finding.to_dict() if hasattr(finding, "to_dict") else dict(getattr(finding, "__dict__", {}))
    return f"| {d.get('severity')} | {d.get('status')} | {d.get('category')} | {d.get('path')} | {d.get('line_number')} | {d.get('marker')} | {d.get('message')} |"


def format_redline_review_report_markdown(report: RedlineReviewReport) -> str:
    decision = enum_value(report.decision)
    critical = [f for f in report.findings if str(enum_value(f.severity)) == "CRITICAL" or str(enum_value(f.status)) == "FAIL"]
    warnings = [f for f in report.findings if str(enum_value(f.severity)) == "WARN" or str(enum_value(f.status)) == "WARN"]
    lines = [
        "# Live switch isolation and red-line review summary",
        "",
        f"Report ID: `{report.report_id}`",
        f"Created at: `{report.created_at}`",
        "",
        "## Decision",
        str(decision),
        "",
        "## Summary",
        "Live switch isolation and red-line review summary.",
        json.dumps(report.summary, ensure_ascii=False),
        "",
        "## Critical blockers",
    ]
    lines += [f"- {f.path}:{f.line_number} {f.marker} {f.message}" for f in critical[:100]] or ["- None"]
    lines += ["", "## Warnings"]
    lines += [f"- {f.path}:{f.line_number} {f.marker} {f.message}" for f in warnings[:100]] or ["- None"]
    lines += ["", "## Findings table", "| Severity | Status | Category | Path | Line | Marker | Message |", "| --- | --- | --- | --- | ---: | --- | --- |"]
    for finding in report.findings[:300]:
        lines.append(format_redline_finding(finding))
    lines += [
        "",
        "## Scheduler isolation",
        "- Scheduler/register preview must remain dry-run only and must not include live execution flags.",
        "",
        "## Dashboard isolation",
        "- Dashboard is read-only and must not expose order-entry or execute-live controls.",
        "",
        "## QMT / xttrader boundary",
        "- This report does not call QMT trading APIs or xttrader.",
        "",
        "## Notification boundary",
        "- This report does not send real notifications.",
        "",
        "## Account query boundary",
        "- This report does not query accounts, funds, positions, orders, or trades.",
        "",
        "## Runtime artifacts / sensitive files",
        "- Runtime artifacts and sensitive files must remain ignored and uncommitted.",
        "",
        "## Manual review checklist",
        "- Confirm READY_FOR_REDLINE_REVIEW is not trading authorization.",
        "- Confirm live trading remains disabled by default.",
        "- Confirm no order was submitted.",
        "- Confirm no real notification was sent.",
        "",
        "## Safety note",
        report.safety_note,
        "",
        "## Next separate stage",
        "Stage 41: 极小资金灰度实盘前只读确认台账（仍不执行）。",
        "",
    ]
    return "\n".join(lines)


def format_redline_review_report_json(report: RedlineReviewReport) -> str:
    return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
