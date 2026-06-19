from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .models import LiveFinalReviewCategory as C, LiveFinalReviewConfig, LiveFinalReviewEvidence, LiveFinalReviewSeverity as Sev, LiveFinalReviewStatus as S

def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists(): return None
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: return {'_load_error': str(exc)}
def _critical(data: dict[str, Any]) -> int:
    try: return int((data.get('summary') or {}).get('critical',0))
    except Exception: return 0
def _evidence(path: Path, cat: C, title: str) -> LiveFinalReviewEvidence:
    data=_load_json(path)
    if data is None: return LiveFinalReviewEvidence(category=cat,status=S.SKIPPED,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} evidence missing; Stage47 needs more evidence but keeps read-only material generation available.")
    if data.get('_load_error'): return LiveFinalReviewEvidence(category=cat,status=S.WARN,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} JSON could not be parsed: {data['_load_error']}")
    decision=str(data.get('decision') or data.get('status') or '').upper(); c=_critical(data)
    if decision in {'NO_GO','BLOCKED'} or c>0: return LiveFinalReviewEvidence(category=cat,status=S.FAIL,severity=Sev.CRITICAL,path=str(path),title=title,summary=f"{title} blocks Stage47 material status: decision={decision or 'UNKNOWN'} critical={c}.",metadata={'decision':decision,'critical':c})
    if decision in {'NEED_MORE_EVIDENCE','UNKNOWN',''}: return LiveFinalReviewEvidence(category=cat,status=S.WARN,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} requires more evidence: decision={decision or 'UNKNOWN'} critical={c}.",metadata={'decision':decision,'critical':c})
    return LiveFinalReviewEvidence(category=cat,status=S.PASS,severity=Sev.INFO,path=str(path),title=title,summary=f"{title} evidence collected: decision={decision} critical={c}.",metadata={'decision':decision,'critical':c})
def _file(path: Path, cat: C, title: str) -> LiveFinalReviewEvidence:
    return LiveFinalReviewEvidence(category=cat,status=S.PASS if path.exists() else S.SKIPPED,severity=Sev.INFO if path.exists() else Sev.WARN,path=str(path),title=title,summary=(f"Found {title}." if path.exists() else f"Missing {title}; needs more evidence."))
def collect_live_final_review_evidence(config: LiveFinalReviewConfig) -> list[LiveFinalReviewEvidence]:
    root=Path(config.repo_root); so=root/config.signoff_dir
    ev=[_evidence(root/config.signature_freeze_dir/'live_signature_freeze.json',C.STAGE43_SIGNATURE_FREEZE,'Stage43 signature/freeze'),_evidence(root/config.env_snapshot_dir/'live_env_snapshot.json',C.STAGE44_ENV_SNAPSHOT,'Stage44 env snapshot'),_evidence(root/config.runbook_dir/'live_runbook.json',C.STAGE45_RUNBOOK,'Stage45 live runbook'),_evidence(so/'live_signoff.json',C.STAGE46_SIGNOFF,'Stage46 live signoff')]
    for rel in ['live_signoff.md','manual_signoff.json','manual_signoff.md','incident_rehearsal.json','incident_rehearsal.md']:
        ev.append(_file(so/rel,C.STAGE46_SIGNOFF,f'Stage46 {rel}'))
    ev.append(_file(root/'redline_review_stage40'/'redline_review.json',C.EVIDENCE_GAP,'Stage40 redline review'))
    ev.append(_file(root/config.validation_logs_dir,C.RUNTIME_ARTIFACT,'validation_logs local runtime directory'))
    gi=root/'.gitignore'; text=gi.read_text(encoding='utf-8') if gi.exists() else ''
    required=['validation_logs/','live_final_review_stage47/','live_final_review/','market_data_test_stage47/','market_data/','reports/','logs/']
    missing=[x for x in required if x not in text]
    ev.append(LiveFinalReviewEvidence(category=C.RUNTIME_ARTIFACT,status=S.PASS if not missing else S.WARN,severity=Sev.INFO if not missing else Sev.WARN,path=str(gi),title='.gitignore',summary='Stage47 runtime artifacts and market_data/reports/logs ignore rules are present.' if not missing else 'Missing ignore rules: '+', '.join(missing),metadata={'missing':missing}))
    return ev
