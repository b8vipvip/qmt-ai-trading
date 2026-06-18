"""Format Stage 32 acceptance reports."""
from __future__ import annotations
import json
from .models import AcceptanceReport

FINAL_ACCEPTANCE_SAFETY_NOTE = "Final acceptance is documentation and dry-run validation only. It does not enable live trading, does not submit orders, and does not call xttrader or QMT trading APIs."

def format_acceptance_report_json(report: AcceptanceReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)

def format_acceptance_report_markdown(report: AcceptanceReport) -> str:
    lines = [
        "# Stage 32 Final Acceptance Report",
        "",
        "## Final acceptance decision",
        f"- Decision: **{report.decision.value}**",
        f"- Success: `{report.success}`",
        f"- Message: {report.message}",
        "",
        "## Summary",
    ]
    for k, v in report.summary.items(): lines.append(f"- {k}: {v}")
    lines += ["", "## Checks"]
    for c in report.checks:
        lines += [f"- **{c.check_id} / {c.title}**: `{c.status.value}` — {c.message}"]
        if c.evidence: lines.append(f"  - Evidence: {c.evidence}")
        if c.remediation: lines.append(f"  - Remediation: {c.remediation}")
    lines += ["", "## Safety note", FINAL_ACCEPTANCE_SAFETY_NOTE, "", "## Next steps", "- Project final acceptance complete; future enhancements require a separately confirmed manual stage and must remain dry-run by default."]
    return "\n".join(lines) + "\n"
