"""Formatting helpers for live readiness audit reports."""
from __future__ import annotations

import json

from .models import AuditCheckResult, AuditReport

SAFETY_NOTE = "This audit report is not permission to trade. Live trading remains disabled unless explicitly enabled in a future audited phase."


def _v(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def format_audit_check_result(check: AuditCheckResult) -> str:
    evidence = "; ".join(check.evidence) if check.evidence else "none"
    return f"- [{_v(check.status)}] {check.check_id}: {check.name} ({_v(check.severity)}) — {check.message} Evidence: {evidence}"


def format_go_no_go_summary(report: AuditReport) -> str:
    return f"Decision: {_v(report.decision)} | PASS={report.pass_count} WARN={report.warn_count} FAIL={report.fail_count} CRITICAL={report.critical_count}"


def format_audit_report_markdown(report: AuditReport) -> str:
    critical = [c for c in report.checks if _v(c.severity) == "CRITICAL" or _v(c.status) == "FAIL"]
    warnings = [c for c in report.checks if _v(c.status) == "WARN"]
    passed = [c for c in report.checks if _v(c.status) == "PASS"]
    remediation = [c for c in report.checks if _v(c.status) in {"FAIL", "WARN"} and c.remediation]
    lines = [
        "# Live Readiness Audit Report",
        "",
        "## Decision",
        f"**{_v(report.decision)}**",
        "",
        "## Summary",
        report.summary,
        format_go_no_go_summary(report),
        "",
        "## Critical findings",
    ]
    lines += [format_audit_check_result(c) for c in critical] or ["- None."]
    lines += ["", "## Warnings"]
    lines += [format_audit_check_result(c) for c in warnings] or ["- None."]
    lines += ["", "## Passed checks"]
    lines += [format_audit_check_result(c) for c in passed] or ["- None."]
    lines += ["", "## Remediation"]
    lines += [f"- {c.check_id}: {c.remediation}" for c in remediation] or ["- None required for current findings."]
    lines += ["", "## Safety note", SAFETY_NOTE, ""]
    return "\n".join(lines)


def format_audit_report_json(report: AuditReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
