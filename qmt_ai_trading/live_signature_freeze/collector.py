from __future__ import annotations
import json
from pathlib import Path
from .models import LiveSignatureFreezeCategory as C, LiveSignatureFreezeConfig, LiveSignatureFreezeEvidence, LiveSignatureFreezeSeverity as Sev, LiveSignatureFreezeStatus as S
from .safety import scan_signature_freeze_text_for_forbidden_markers

def _ev(i,cat,status,sev,path,title,summary,**md): return LiveSignatureFreezeEvidence(i,cat,status,sev,str(path),title,summary,md)
def _read_json(path: Path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: return {"_error": str(exc)}
def _critical_count(data):
    s=data.get('summary') or {}; return int(s.get('critical') or s.get('critical_count') or 0)
def _decision(data): return str(data.get('decision') or data.get('status') or '').upper()

def collect_live_signature_freeze_evidence(config: LiveSignatureFreezeConfig):
    root=Path(config.repo_root); evidence=[]; items=[]
    review=root/config.review_dir; ledger=root/config.ledger_dir; redline=root/config.redline_review_dir
    paths=[review/'live_gray_review.json', review/'live_gray_review.md', review/'readonly_rehearsal.json', review/'readonly_rehearsal.md', ledger/'live_gray_ledger.json', redline/'redline_review.json']
    for path in paths:
        if not path.exists():
            evidence.append(_ev(f'stage43-missing-{len(evidence)+1}', C.SYSTEM, S.SKIPPED, Sev.WARN, path, 'Missing evidence', f'{path} is missing; Stage43 can still generate materials but needs more evidence.'))
            continue
        if path.suffix.lower()=='.json':
            data=_read_json(path); dec=_decision(data); crit=_critical_count(data)
            cat=C.STAGE42_HUMAN_REVIEW if 'live_gray_review' in str(path) or 'readonly_rehearsal' in str(path) else C.STAGE41_LEDGER if 'ledger' in str(path) else C.STAGE40_REDLINE_REVIEW
            if data.get('_error'):
                evidence.append(_ev(f'stage43-json-error-{len(evidence)+1}', cat, S.WARN, Sev.WARN, path, 'Unreadable JSON', data['_error']))
            elif (cat==C.STAGE42_HUMAN_REVIEW and (dec=='NO_GO' or crit>0)) or (cat==C.STAGE41_LEDGER and (dec=='BLOCKED' or crit>0)) or (cat==C.STAGE40_REDLINE_REVIEW and (dec=='BLOCKED' or crit>0)):
                evidence.append(_ev(f'stage43-blocked-{len(evidence)+1}', cat, S.FAIL, Sev.CRITICAL, path, 'Blocking evidence', f'decision={dec or "UNKNOWN"} critical={crit}', decision=dec, critical=crit))
            elif cat==C.STAGE42_HUMAN_REVIEW and dec=='NEED_MORE_EVIDENCE' and crit==0:
                evidence.append(_ev(f'stage43-need-evidence-{len(evidence)+1}', cat, S.WARN, Sev.WARN, path, 'Stage42 needs more evidence', 'Stage42 NEED_MORE_EVIDENCE with critical=0; Stage43 remains NEED_MORE_EVIDENCE, not NO_GO.', decision=dec, critical=crit))
            else:
                evidence.append(_ev(f'stage43-pass-{len(evidence)+1}', cat, S.PASS, Sev.INFO, path, 'Evidence available', f'decision={dec or "UNKNOWN"} critical={crit}', decision=dec, critical=crit))
        else:
            evidence.append(_ev(f'stage43-md-{len(evidence)+1}', C.STAGE42_HUMAN_REVIEW, S.PASS, Sev.INFO, path, 'Markdown evidence available', f'{path.name} is available for manual review.'))
        if path.is_file() and path.stat().st_size < 500_000:
            items.extend(scan_signature_freeze_text_for_forbidden_markers(path.read_text(encoding='utf-8', errors='replace'), path))
    val=root/config.validation_logs_dir
    evidence.append(_ev('stage43-validation-logs', C.RUNTIME_ARTIFACT, S.SKIPPED if not val.exists() else S.WARN, Sev.WARN, val, 'Validation logs ignored', 'validation_logs is a local runtime artifact and remains ignored.'))
    return evidence, items
