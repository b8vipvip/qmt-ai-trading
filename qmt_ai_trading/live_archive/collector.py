from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .models import LiveArchiveCategory as C, LiveArchiveConfig, LiveArchiveEvidence, LiveArchiveSeverity as Sev, LiveArchiveStatus as S

def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists(): return None
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: return {'_load_error': str(exc)}
def _critical(data: dict[str, Any]) -> int:
    try: return int((data.get('summary') or {}).get('critical',0))
    except Exception: return 0
def _evidence(path: Path, cat: C, title: str) -> LiveArchiveEvidence:
    data=_load_json(path)
    if data is None: return LiveArchiveEvidence(category=cat,status=S.SKIPPED,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} evidence missing; Stage48 needs more evidence but keeps read-only archive generation available.")
    if data.get('_load_error'): return LiveArchiveEvidence(category=cat,status=S.WARN,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} JSON could not be parsed: {data['_load_error']}")
    decision=str(data.get('decision') or data.get('status') or '').upper(); c=_critical(data)
    if decision in {'NO_GO','BLOCKED'} or c>0: return LiveArchiveEvidence(category=cat,status=S.FAIL,severity=Sev.CRITICAL,path=str(path),title=title,summary=f"{title} blocks Stage48 material status: decision={decision or 'UNKNOWN'} critical={c}.",metadata={'decision':decision,'critical':c})
    if decision in {'NEED_MORE_EVIDENCE','UNKNOWN',''}: return LiveArchiveEvidence(category=cat,status=S.WARN,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} requires more evidence: decision={decision or 'UNKNOWN'} critical={c}.",metadata={'decision':decision,'critical':c})
    return LiveArchiveEvidence(category=cat,status=S.PASS,severity=Sev.INFO,path=str(path),title=title,summary=f"{title} evidence collected: decision={decision} critical={c}.",metadata={'decision':decision,'critical':c})
def _file(path: Path, cat: C, title: str) -> LiveArchiveEvidence:
    return LiveArchiveEvidence(category=cat,status=S.PASS if path.exists() else S.SKIPPED,severity=Sev.INFO if path.exists() else Sev.WARN,path=str(path),title=title,summary=(f"Found {title}." if path.exists() else f"Missing {title}; needs more evidence."))
def collect_live_archive_evidence(config: LiveArchiveConfig) -> list[LiveArchiveEvidence]:
    root=Path(config.repo_root); fr=root/config.final_review_dir
    ev=[_evidence(fr/'live_final_review.json',C.STAGE47_FINAL_REVIEW,'Stage47 final review'),_evidence(root/config.signoff_dir/'live_signoff.json',C.STAGE46_SIGNOFF,'Stage46 live signoff'),_evidence(root/config.runbook_dir/'live_runbook.json',C.STAGE45_RUNBOOK,'Stage45 live runbook'),_evidence(root/config.env_snapshot_dir/'live_env_snapshot.json',C.STAGE44_ENV_SNAPSHOT,'Stage44 env snapshot')]
    for rel,title in [('live_final_review.md','Stage47 final review Markdown'),('signature_verification.json','Stage47 signature verification JSON'),('signature_verification.md','Stage47 signature verification Markdown'),('evidence_gap_report.json','Stage47 evidence gap JSON'),('evidence_gap_report.md','Stage47 evidence gap Markdown'),('next_readonly_plan.json','Stage47 next readonly plan JSON'),('next_readonly_plan.md','Stage47 next readonly plan Markdown')]: ev.append(_file(fr/rel,C.STAGE47_FINAL_REVIEW,title))
    for d,f,t,c in [(config.signoff_dir,'live_signoff.json','Stage46 signoff file',C.STAGE46_SIGNOFF),(config.runbook_dir,'live_runbook.json','Stage45 runbook file',C.STAGE45_RUNBOOK),(config.env_snapshot_dir,'live_env_snapshot.json','Stage44 environment snapshot file',C.STAGE44_ENV_SNAPSHOT)]: ev.append(_file(root/d/f,c,t))
    ev.append(_file(root/config.validation_logs_dir,C.RUNTIME_ARTIFACT,'validation_logs local runtime directory'))
    gi=root/'.gitignore'; text=gi.read_text(encoding='utf-8') if gi.exists() else ''
    required=['validation_logs/','live_archive_stage48/','live_archive/','market_data_test_stage48/','market_data/','reports/','logs/']
    missing=[x for x in required if x not in text]
    ev.append(LiveArchiveEvidence(category=C.RUNTIME_ARTIFACT,status=S.PASS if not missing else S.WARN,severity=Sev.INFO if not missing else Sev.WARN,path=str(gi),title='.gitignore',summary='Stage48 runtime artifacts and market_data/reports/logs ignore rules are present.' if not missing else 'Missing ignore rules: '+', '.join(missing),metadata={'missing':missing}))
    return ev
