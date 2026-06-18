from __future__ import annotations
import json
from .models import LiveManualPrepEvidence, LiveManualPrepPackage

def format_live_manual_prep_evidence(evidence: LiveManualPrepEvidence)->str:
    st=evidence.status.value if hasattr(evidence.status,"value") else str(evidence.status); typ=evidence.evidence_type.value if hasattr(evidence.evidence_type,"value") else str(evidence.evidence_type)
    return f"| {typ} | {st} | {evidence.severity} | {evidence.source_path} | {evidence.summary} | {evidence.blocked_reason} |"
def format_live_manual_prep_package_json(package: LiveManualPrepPackage)->str:
    return json.dumps(package.to_dict(), ensure_ascii=False, indent=2)
def format_live_manual_prep_package_markdown(package: LiveManualPrepPackage)->str:
    d=package.to_dict(); lines=["# Live manual approval prep summary","",f"Package ID: `{d['package_id']}`",f"Created at: `{d['created_at']}`","", "## Decision", f"- Decision: **{d['decision']}**", "- READY_FOR_SIGNOFF means ready for human signoff review only; it is not live trading authorization.", "", "## Required evidence", "- Gray Decision Package / Live Gray Readiness / Gray Rehearsal / Live Readiness Audit / Risk Gate / Human Approval / Paper Trading / Monitoring / Data Quality / Agent Research / Notification Dry Run / Dashboard / Final Acceptance", "", "## Evidence table", "| Type | Status | Severity | Source | Summary | Blocked reason |", "| --- | --- | --- | --- | --- | --- |"]
    lines += [format_live_manual_prep_evidence(e) for e in package.evidence]
    lines += ["", "## Blocked reasons"] + [f"- {x}" for x in (d['blocked_reasons'] or ["None"])]
    lines += ["", "## Warnings"] + [f"- {x}" for x in (d['warnings'] or ["None"])]
    lines += ["", "## Manual checklist"] + [f"- [ ] {x}" for x in d['checklist']]
    lines += ["", "## Forbidden items"] + [f"- {x}" for x in d['forbidden_items']]
    lines += ["", "## Residual risks"] + [f"- {x}" for x in d['residual_risks']]
    lines += ["", "## Signoff placeholders"] + [f"- {x}" for x in d['signoff_placeholders']]
    lines += ["", "## Safety note", d['safety_note'], "", "## Next separate stage", "阶段三十八：极小资金灰度只读环境核验（仍不下单）。"]
    return "\n".join(lines)+"\n"
