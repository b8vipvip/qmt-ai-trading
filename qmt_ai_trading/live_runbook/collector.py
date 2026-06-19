from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .models import LiveRunbookCategory as C, LiveRunbookConfig, LiveRunbookEvidence, LiveRunbookSeverity as Sev, LiveRunbookStatus as S

def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists(): return None
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: return {"_load_error": str(exc)}

def _count_critical(data: dict[str, Any]) -> int:
    summary=data.get('summary') or {}; n=summary.get('critical',0)
    try: n=int(n)
    except Exception: n=0
    for key in ('evidence','items','config_freeze_review','environment_snapshot'):
        for item in data.get(key) or []:
            if str(item.get('severity','')).upper()=='CRITICAL': n+=1
    return n

def _evidence(path: Path, cat: C, title: str, nogo_values: set[str]) -> LiveRunbookEvidence:
    data=_load_json(path)
    if data is None:
        return LiveRunbookEvidence(category=cat,status=S.SKIPPED,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} evidence missing; Stage45 can still generate read-only materials but needs more evidence.")
    if data.get('_load_error'):
        return LiveRunbookEvidence(category=cat,status=S.WARN,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} JSON could not be parsed: {data['_load_error']}")
    decision=str(data.get('decision') or data.get('status') or '').upper(); critical=_count_critical(data)
    if decision in nogo_values or critical>0:
        return LiveRunbookEvidence(category=cat,status=S.FAIL,severity=Sev.CRITICAL,path=str(path),title=title,summary=f"{title} blocks Stage45 material readiness: decision={decision or 'UNKNOWN'} critical={critical}.",metadata={'decision':decision,'critical':critical})
    if decision in {'NEED_MORE_EVIDENCE','BLOCKED','NO_GO'}:
        return LiveRunbookEvidence(category=cat,status=S.WARN,severity=Sev.WARN,path=str(path),title=title,summary=f"{title} requires more evidence: decision={decision} critical={critical}.",metadata={'decision':decision,'critical':critical})
    return LiveRunbookEvidence(category=cat,status=S.PASS,severity=Sev.INFO,path=str(path),title=title,summary=f"{title} evidence collected: decision={decision or 'UNKNOWN'} critical={critical}.",metadata={'decision':decision,'critical':critical})

def collect_live_runbook_evidence(config: LiveRunbookConfig) -> list[LiveRunbookEvidence]:
    root=Path(config.repo_root)
    ev=[
        _evidence(root/config.ledger_dir/'live_gray_ledger.json', C.STAGE41_LEDGER, 'Stage41 ledger', {'BLOCKED','NO_GO'}),
        _evidence(root/config.review_dir/'live_gray_review.json', C.STAGE42_HUMAN_REVIEW, 'Stage42 human review', {'NO_GO'}),
        _evidence(root/config.signature_freeze_dir/'live_signature_freeze.json', C.STAGE43_SIGNATURE_FREEZE, 'Stage43 signature/freeze', {'NO_GO'}),
        _evidence(root/config.env_snapshot_dir/'live_env_snapshot.json', C.STAGE44_ENV_SNAPSHOT, 'Stage44 env snapshot', {'NO_GO'}),
    ]
    for rel in ['live_env_snapshot.md','readonly_environment_snapshot.json','readonly_environment_snapshot.md']:
        p=root/config.env_snapshot_dir/rel
        ev.append(LiveRunbookEvidence(category=C.STAGE44_ENV_SNAPSHOT,status=S.PASS if p.exists() else S.SKIPPED,severity=Sev.INFO if p.exists() else Sev.WARN,path=str(p),title=rel,summary=(f"Found Stage44 companion file {rel}." if p.exists() else f"Missing Stage44 companion file {rel}.")))
    gi=root/'.gitignore'
    text=gi.read_text(encoding='utf-8') if gi.exists() else ''
    required=['validation_logs/','live_runbook_stage45/','live_runbook/','market_data_test_stage45/']
    missing=[x for x in required if x not in text]
    ev.append(LiveRunbookEvidence(category=C.RUNTIME_ARTIFACT,status=S.PASS if not missing else S.WARN,severity=Sev.INFO if not missing else Sev.WARN,path=str(gi),title='.gitignore',summary='Stage45 runtime artifacts are ignored.' if not missing else 'Missing ignore rules: '+', '.join(missing),metadata={'missing':missing}))
    return ev
