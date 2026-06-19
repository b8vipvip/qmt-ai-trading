from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .models import LiveSignoffCategory as C, LiveSignoffConfig, LiveSignoffEvidence, LiveSignoffSeverity as Sev, LiveSignoffStatus as S

def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists(): return None
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: return {'_load_error': str(exc)}
def _critical(data: dict[str, Any]) -> int:
    n=0
    try: n += int((data.get('summary') or {}).get('critical',0))
    except Exception: pass
    def walk(x):
        nonlocal n
        if isinstance(x, dict):
            if str(x.get('severity','')).upper()=='CRITICAL': n += 1
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(data); return n
def _evidence(path: Path, cat: C, title: str) -> LiveSignoffEvidence:
    data=_load_json(path)
    if data is None: return LiveSignoffEvidence(category=cat,status=S.SKIPPED,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} evidence missing; Stage46 can generate read-only materials but needs more evidence.")
    if data.get('_load_error'): return LiveSignoffEvidence(category=cat,status=S.WARN,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} JSON could not be parsed: {data['_load_error']}")
    decision=str(data.get('decision') or data.get('status') or '').upper(); c=_critical(data)
    if decision in {'NO_GO','BLOCKED'} or c>0: return LiveSignoffEvidence(category=cat,status=S.FAIL,severity=Sev.CRITICAL,path=str(path),title=title,summary=f"{title} blocks Stage46 material status: decision={decision or 'UNKNOWN'} critical={c}.",metadata={'decision':decision,'critical':c})
    if decision in {'NEED_MORE_EVIDENCE','UNKNOWN',''}: return LiveSignoffEvidence(category=cat,status=S.WARN,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} requires more evidence: decision={decision or 'UNKNOWN'} critical={c}.",metadata={'decision':decision,'critical':c})
    return LiveSignoffEvidence(category=cat,status=S.PASS,severity=Sev.INFO,path=str(path),title=title,summary=f"{title} evidence collected: decision={decision} critical={c}.",metadata={'decision':decision,'critical':c})
def _file(path: Path, cat: C, title: str) -> LiveSignoffEvidence:
    return LiveSignoffEvidence(category=cat,status=S.PASS if path.exists() else S.SKIPPED,severity=Sev.INFO if path.exists() else Sev.WARN,path=str(path),title=title,summary=(f"Found {title}." if path.exists() else f"Missing {title}; needs more evidence."))
def collect_live_signoff_evidence(config: LiveSignoffConfig) -> list[LiveSignoffEvidence]:
    root=Path(config.repo_root); rb=root/config.runbook_dir
    ev=[_evidence(root/config.review_dir/'live_gray_review.json',C.STAGE42_HUMAN_REVIEW,'Stage42 human review'),_evidence(root/config.signature_freeze_dir/'live_signature_freeze.json',C.STAGE43_SIGNATURE_FREEZE,'Stage43 signature/freeze'),_evidence(root/config.env_snapshot_dir/'live_env_snapshot.json',C.STAGE44_ENV_SNAPSHOT,'Stage44 env snapshot'),_evidence(rb/'live_runbook.json',C.STAGE45_RUNBOOK,'Stage45 live runbook')]
    for rel in ['live_runbook.md','manual_rehearsal.json','manual_rehearsal.md','incident_playbook.json','incident_playbook.md']:
        ev.append(_file(rb/rel,C.STAGE45_RUNBOOK,f'Stage45 {rel}'))
    gi=root/'.gitignore'; text=gi.read_text(encoding='utf-8') if gi.exists() else ''
    missing=[x for x in ['validation_logs/','live_signoff_stage46/','live_signoff/','market_data_test_stage46/'] if x not in text]
    ev.append(LiveSignoffEvidence(category=C.RUNTIME_ARTIFACT,status=S.PASS if not missing else S.WARN,severity=Sev.INFO if not missing else Sev.WARN,path=str(gi),title='.gitignore',summary='Stage46 runtime artifacts are ignored.' if not missing else 'Missing ignore rules: '+', '.join(missing),metadata={'missing':missing}))
    return ev
