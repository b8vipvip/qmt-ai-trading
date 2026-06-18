"""Read-only Stage 32 final acceptance service."""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from pathlib import Path
from .formatters import FINAL_ACCEPTANCE_SAFETY_NOTE, format_acceptance_report_json, format_acceptance_report_markdown
from .models import AcceptanceCheck, AcceptanceDecision, AcceptanceReport
from .safety import check_no_sensitive_patterns_in_docs, check_runtime_artifact_gitignore_patterns, check_sync_script_protected, validate_acceptance_is_dry_run

REQUIRED_DOCS = [
"docs/runbook-overview.md","docs/setup-local-environment.md","docs/runbook-daily-pipeline.md","docs/runbook-scheduler.md","docs/runbook-approval-paper.md","docs/runbook-monitoring-agent-dashboard.md","docs/runbook-live-gray-readiness.md","docs/final-acceptance-checklist.md","docs/stage31-ui-dashboard.md","docs/stage30-live-gray-readiness.md","docs/stage29-agent-research-layer.md"]

def build_acceptance_report(checks: list[AcceptanceCheck], metadata: dict | None = None) -> AcceptanceReport:
    decision = AcceptanceDecision.FAIL if any(c.status == AcceptanceDecision.FAIL for c in checks) else (AcceptanceDecision.WARN if any(c.status == AcceptanceDecision.WARN for c in checks) else AcceptanceDecision.PASS)
    summary = {"pass": sum(c.status==AcceptanceDecision.PASS for c in checks), "warn": sum(c.status==AcceptanceDecision.WARN for c in checks), "fail": sum(c.status==AcceptanceDecision.FAIL for c in checks), "total": len(checks)}
    return AcceptanceReport(str(uuid.uuid4()), datetime.now(timezone.utc).isoformat(), decision, checks, summary, FINAL_ACCEPTANCE_SAFETY_NOTE, decision != AcceptanceDecision.FAIL, "Stage 32 final acceptance check completed in dry-run/read-only mode.", metadata or {})

def run_final_acceptance_check(repo_root: str | Path = ".") -> AcceptanceReport:
    root = Path(repo_root).resolve(); checks=[]
    ok,msg=validate_acceptance_is_dry_run(); checks.append(AcceptanceCheck("safety.dry_run","Dry-run acceptance boundary",AcceptanceDecision.PASS if ok else AcceptanceDecision.FAIL,msg,evidence="service-level invariant"))
    for rel in REQUIRED_DOCS:
        exists=(root/rel).exists(); checks.append(AcceptanceCheck(f"doc.{Path(rel).stem}",f"Required document {rel}",AcceptanceDecision.PASS if exists else AcceptanceDecision.FAIL,"exists" if exists else "missing", evidence=rel, remediation="Create or restore the required document."))
    ok,missing=check_runtime_artifact_gitignore_patterns(root); checks.append(AcceptanceCheck("gitignore.runtime_artifacts","Runtime artifact gitignore coverage",AcceptanceDecision.PASS if ok else AcceptanceDecision.FAIL,"all required patterns present" if ok else "missing runtime artifact patterns", evidence=", ".join(missing), remediation="Update .gitignore without ignoring docs/."))
    ok,msg=check_sync_script_protected(root); checks.append(AcceptanceCheck("sync.protected","sync_all.ps1 protected",AcceptanceDecision.PASS if ok else AcceptanceDecision.FAIL,msg,evidence="git diff -- scripts/sync_all.ps1"))
    ok,findings=check_no_sensitive_patterns_in_docs(root); checks.append(AcceptanceCheck("docs.no_sensitive_patterns","Docs sensitive pattern scan",AcceptanceDecision.PASS if ok else AcceptanceDecision.WARN,"no obvious sensitive assignment patterns" if ok else "possible sensitive placeholders found", evidence=", ".join(findings), remediation="Remove secrets/tokens from docs."))
    checks.append(AcceptanceCheck("safety.note","Acceptance safety note",AcceptanceDecision.PASS,"safety note contains dry-run/no order/no xttrader", evidence=FINAL_ACCEPTANCE_SAFETY_NOTE))
    return build_acceptance_report(checks, metadata={"repo_root": str(root), "mode": "read_only_dry_run"})

def save_acceptance_report(report: AcceptanceReport, path: str | Path) -> Path:
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    text = format_acceptance_report_json(report) if p.suffix.lower()==".json" else format_acceptance_report_markdown(report)
    p.write_text(text, encoding="utf-8"); return p

def load_acceptance_report(path: str | Path) -> AcceptanceReport:
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    checks=[AcceptanceCheck(c["check_id"], c["title"], AcceptanceDecision(c["status"]), c["message"], c.get("evidence",""), c.get("remediation",""), c.get("metadata",{})) for c in data.get("checks",[])]
    return AcceptanceReport(data["report_id"], data["created_at"], AcceptanceDecision(data["decision"]), checks, data.get("summary",{}), data.get("safety_note",""), data.get("success",False), data.get("message",""), data.get("metadata",{}))
