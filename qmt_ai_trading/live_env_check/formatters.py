from __future__ import annotations
import json
from .models import LiveEnvCheckReport, LiveEnvCheckScope as S

def format_live_env_check_item(check):
    status=getattr(check.status,"value",check.status); scope=getattr(check.scope,"value",check.scope)
    ev="; ".join(check.evidence) if check.evidence else "n/a"
    return f"- **[{status}] {scope} / {check.check_id}**: {check.title} — {check.message}\n  - Evidence: {ev}\n  - Remediation: {check.remediation or 'n/a'}"

def _section(report, title, scopes):
    body=[format_live_env_check_item(c) for c in report.checks if (getattr(c.scope,"value",c.scope) in scopes)]
    return f"## {title}\n" + ("\n".join(body) if body else "- No checks in this section.")

def format_live_env_check_report_markdown(report: LiveEnvCheckReport) -> str:
    decision=getattr(report.decision,"value",report.decision)
    lines=["# Live environment read-only check summary", "", f"- Report ID: {report.report_id}", f"- Created at: {report.created_at}", f"- Success: {report.success}", "", "## Decision", f"**{decision}**", "", report.message, "", _section(report,"System/file checks", ["SYSTEM","FILES"]), "", _section(report,"Git/runtime artifact checks", ["GIT","SECURITY"]), "", _section(report,"Config checks", ["CONFIG"]), "", _section(report,"Scheduler preview checks", ["SCHEDULER"]), "", _section(report,"Evidence checks", ["RISK","APPROVAL","PAPER","MONITORING","DATA_QUALITY","AGENT","NOTIFICATION","DASHBOARD","LIVE_MANUAL_PREP"]), "", "## Blocked reasons"]
    lines += [f"- {x}" for x in report.blocked_reasons] or ["- None"]
    lines += ["", "## Warnings"] + ([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["", "## Safety note", report.safety_note, "", "## Next separate stage", "阶段三十九：极小资金灰度最终人工授权包（仍不执行）。READY_FOR_ENV_REVIEW does not enable live trading or authorize orders."]
    return "\n".join(lines)+"\n"

def format_live_env_check_report_json(report: LiveEnvCheckReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
