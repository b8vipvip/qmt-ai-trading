from __future__ import annotations
import json
from .models import FinalAuthorizationEvidence, FinalAuthorizationPackage

def format_final_authorization_evidence(evidence: FinalAuthorizationEvidence)->str:
    st=getattr(evidence.status,"value",evidence.status); typ=getattr(evidence.evidence_type,"value",evidence.evidence_type)
    return f"| {typ} | {st} | {evidence.severity} | {evidence.source_path} | {evidence.summary} | {evidence.blocked_reason} |"
def format_final_authorization_package_json(package: FinalAuthorizationPackage)->str:
    return json.dumps(package.to_dict(), ensure_ascii=False, indent=2)
def format_final_authorization_package_markdown(package: FinalAuthorizationPackage)->str:
    d=package.to_dict(); lines=["# Final manual authorization package summary","",f"Package ID: `{d['package_id']}`",f"Created at: `{d['created_at']}`","","## Decision",f"- Decision: **{d['decision']}**","- READY_FOR_FINAL_SIGNOFF_REVIEW means ready for human final signoff review only; it is not live trading authorization.","","## Required evidence","- Live Env Check / Live Manual Prep / Gray Decision Package / Gray Rehearsal / Live Gray Readiness / Live Readiness Audit / Risk Gate / Human Approval / Paper Trading / Monitoring / Data Quality / Agent Research / Notification Dry Run / Dashboard / Final Acceptance","","## Evidence table","| Type | Status | Severity | Source | Summary | Blocked reason |","| --- | --- | --- | --- | --- | --- |"]
    lines += [format_final_authorization_evidence(e) for e in package.evidence]
    lines += ["", "## Blocked reasons"] + [f"- {x}" for x in (d['blocked_reasons'] or ["None"])]
    lines += ["", "## Warnings"] + [f"- {x}" for x in (d['warnings'] or ["None"])]
    lines += ["", "## Manual checklist"] + [f"- [ ] {x}" for x in d['checklist']]
    lines += ["", "## Forbidden items"] + [f"- {x}" for x in d['forbidden_items']]
    lines += ["", "## Residual risks"] + [f"- {x}" for x in d['residual_risks']]
    lines += ["", "## Future stage requirements"] + [f"- {x}" for x in d['future_stage_requirements']]
    lines += ["", "## Signoff placeholders"] + [f"- {x}" for x in d['signoff_placeholders']]
    lines += ["", "## Safety note", d['safety_note'], "", "## Next separate stage", "阶段四十：实盘开关隔离与最终红线复核（仍默认关闭）。"]
    return "\n".join(lines)+"\n"
