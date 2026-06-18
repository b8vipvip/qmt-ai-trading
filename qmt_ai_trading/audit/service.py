"""Service layer for Stage 23 live-readiness audit."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from . import checks as audit_checks
from .formatters import format_audit_report_json
from .models import AuditCheckResult, AuditReport, AuditSeverity, AuditStatus, GoNoGoDecision, LiveReadinessPolicy


def build_live_readiness_policy(**kwargs) -> LiveReadinessPolicy:
    return LiveReadinessPolicy(**kwargs)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _status(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _severity(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def summarize_audit_report(report: AuditReport) -> str:
    return (
        f"Decision={_status(report.decision)}; checks={report.total_checks}; "
        f"pass={report.pass_count}; warn={report.warn_count}; fail={report.fail_count}; "
        f"critical={report.critical_count}."
    )


def run_live_readiness_audit(project_root: str | Path = ".", policy: LiveReadinessPolicy | None = None) -> AuditReport:
    policy = policy or LiveReadinessPolicy()
    root = Path(project_root).resolve()
    check_functions = [
        audit_checks.check_required_docs,
        audit_checks.check_roadmap_stage_alignment,
        audit_checks.check_architecture_safety_rules,
        audit_checks.check_sync_script_protected,
        audit_checks.check_gitignore_runtime_dirs,
        audit_checks.check_live_trading_disabled,
        audit_checks.check_no_xttrader_import_outside_gateway,
        audit_checks.check_no_direct_order_call_outside_gateway,
        audit_checks.check_risk_gate_exists,
        audit_checks.check_human_approval_exists,
        audit_checks.check_paper_trading_exists,
        audit_checks.check_no_sensitive_patterns_in_tracked_files,
        audit_checks.check_runtime_dirs_not_tracked,
        audit_checks.check_pipeline_dry_run_report_capable,
        audit_checks.check_approval_and_paper_blocking_logic,
    ]
    results: list[AuditCheckResult] = []
    for fn in check_functions:
        try:
            results.append(fn(root))
        except Exception as exc:
            results.append(AuditCheckResult(fn.__name__, fn.__name__, AuditStatus.FAIL, AuditSeverity.ERROR, "Audit check crashed safely without executing trading code.", [type(exc).__name__], "Fix the audit check so it can inspect repository state.", {"error_type": type(exc).__name__}))

    pass_count = sum(_status(c.status) == AuditStatus.PASS.value for c in results)
    warn_count = sum(_status(c.status) == AuditStatus.WARN.value for c in results)
    fail_count = sum(_status(c.status) == AuditStatus.FAIL.value for c in results)
    critical_count = sum(_severity(c.severity) == AuditSeverity.CRITICAL.value and _status(c.status) in {AuditStatus.FAIL.value, AuditStatus.WARN.value} for c in results)
    has_fail_or_critical = fail_count > 0 or critical_count > 0
    decision = GoNoGoDecision.NO_GO
    reason = "GO disabled by policy"
    if has_fail_or_critical:
        reason = "NO-GO because one or more FAIL/CRITICAL findings exist"
    elif policy.allow_go:
        decision = GoNoGoDecision.GO
        reason = "GO allowed by policy and no FAIL/CRITICAL findings exist"

    report = AuditReport(
        report_id=f"live-readiness-{uuid4().hex}",
        created_at=_now(),
        project_root=str(root),
        decision=decision,
        total_checks=len(results),
        pass_count=pass_count,
        warn_count=warn_count,
        fail_count=fail_count,
        critical_count=critical_count,
        checks=results,
        metadata={"policy": policy.to_dict(), "decision_reason": reason, "no_qmt_called": True, "no_xttrader_called": True, "no_order_submitted": True},
    )
    report.summary = summarize_audit_report(report) + f" {reason}."
    return report


def save_audit_report(report: AuditReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(format_audit_report_json(report), encoding="utf-8")
    else:
        from .formatters import format_audit_report_markdown
        path.write_text(format_audit_report_markdown(report), encoding="utf-8")
    return path


def load_audit_report(path: str | Path) -> AuditReport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    check_objs = [AuditCheckResult(**c) for c in data.get("checks", [])]
    data["checks"] = check_objs
    return AuditReport(**data)
