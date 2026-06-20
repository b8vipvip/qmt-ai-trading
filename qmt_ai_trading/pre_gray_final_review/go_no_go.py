from __future__ import annotations
from .models import *

def generate_go_no_go_draft(evidence: list[PreGrayFinalReviewEvidence], blockers: list[NoGoBlockerItem]|None=None) -> GoNoGoDraftDecision:
    if any(e.metadata.get('decision')=='NO_GO' for e in evidence): return GoNoGoDraftDecision.NO_GO_DRAFT
    if any(e.severity==PreGrayFinalReviewSeverity.CRITICAL or int(e.metadata.get('critical') or 0)>0 for e in evidence): return GoNoGoDraftDecision.NO_GO_DRAFT
    if blockers and any(b.active and b.severity==PreGrayFinalReviewSeverity.CRITICAL for b in blockers): return GoNoGoDraftDecision.NO_GO_DRAFT
    required=(PreGrayFinalReviewCategory.MANIFEST_HASH_RECHECK,PreGrayFinalReviewCategory.PRE_RUN_CHECKLIST_RECHECK,PreGrayFinalReviewCategory.HUMAN_APPROVAL_FINAL_RECHECK,PreGrayFinalReviewCategory.REGISTER_PREVIEW_RECHECK)
    if any(e.category in required and e.status!=PreGrayFinalReviewStatus.PASS for e in evidence): return GoNoGoDraftDecision.NEED_MORE_EVIDENCE_DRAFT
    stages=[e for e in evidence if e.category.name.startswith('STAGE') and e.category not in (PreGrayFinalReviewCategory.STAGE61_API_GATEWAY_PLAN,)]
    if len(stages)<5 or any(e.metadata.get('decision') in (None,'NEED_MORE_EVIDENCE') for e in stages): return GoNoGoDraftDecision.NEED_MORE_EVIDENCE_DRAFT
    return GoNoGoDraftDecision.GO_DRAFT
