from __future__ import annotations
import json
from pathlib import Path
from .models import LiveGrayLedgerCategory as C, LiveGrayLedgerConfig, LiveGrayLedgerEvidence, LiveGrayLedgerSeverity as Sev, LiveGrayLedgerStatus as S
from .safety import scan_ledger_text_for_forbidden_markers

def _ev(i, cat, status, sev, path, title, summary, **md): return LiveGrayLedgerEvidence(i, cat, status, sev, str(path), title, summary, md)
def _read_json(path: Path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: return {"_error": str(exc)}
def _exists_dir(root: Path, rel: str, cat: C, title: str):
    p=root/rel
    if p.exists(): return _ev(f"stage41-{cat.value.lower()}", cat, S.PASS, Sev.INFO, p, title, "Evidence directory exists.")
    return _ev(f"stage41-{cat.value.lower()}-missing", cat, S.SKIPPED, Sev.WARN, p, title, "Evidence directory is missing; manual confirmation may be needed.")

def collect_live_gray_ledger_evidence(config: LiveGrayLedgerConfig):
    root=Path(config.repo_root)
    evidence=[
        _exists_dir(root, config.live_manual_prep_dir, C.STAGE37_MANUAL_PREP, "Stage37 manual prep"),
        _exists_dir(root, config.live_env_check_dir, C.STAGE38_ENV_CHECK, "Stage38 live env check"),
        _exists_dir(root, config.final_authorization_dir, C.STAGE39_FINAL_AUTHORIZATION, "Stage39 final authorization"),
    ]
    red_dir=root/config.redline_review_dir; red_json=red_dir/'redline_review.json'; red_md=red_dir/'redline_review.md'
    if red_json.exists():
        data=_read_json(red_json); decision=data.get('decision'); summary=data.get('summary') or {}; crit=int(summary.get('critical') or summary.get('critical_count') or 0)
        if decision == 'BLOCKED' or crit > 0:
            evidence.append(_ev('stage41-stage40-redline-json', C.STAGE40_REDLINE_REVIEW, S.FAIL, Sev.CRITICAL, red_json, 'Stage40 redline JSON', f'Redline decision={decision}; critical={crit}.', decision=decision, critical=crit))
        elif decision == 'READY_FOR_REDLINE_REVIEW' and crit == 0:
            evidence.append(_ev('stage41-stage40-redline-json', C.STAGE40_REDLINE_REVIEW, S.PASS, Sev.INFO, red_json, 'Stage40 redline JSON', 'Stage40 redline review is ready for manual redline review with zero critical findings.', decision=decision, critical=crit))
        else:
            evidence.append(_ev('stage41-stage40-redline-json', C.STAGE40_REDLINE_REVIEW, S.WARN, Sev.WARN, red_json, 'Stage40 redline JSON', f'Redline decision={decision}; critical={crit}; manual review needed.', decision=decision, critical=crit))
    else:
        evidence.append(_ev('stage41-stage40-redline-json-missing', C.STAGE40_REDLINE_REVIEW, S.WARN, Sev.WARN, red_json, 'Stage40 redline JSON', 'redline_review.json is missing.'))
    if red_md.exists(): evidence.append(_ev('stage41-stage40-redline-md', C.STAGE40_REDLINE_REVIEW, S.PASS, Sev.INFO, red_md, 'Stage40 redline Markdown', 'redline_review.md exists.'))
    for rel, cat, title in [(config.gray_decision_dir,C.SYSTEM,'Stage40 gray decision'),(config.gray_rehearsal_dir,C.SYSTEM,'Stage40 gray rehearsal'),(config.notification_dryrun_dir,C.NOTIFICATION,'Stage40 notification dry-run'),(config.validation_logs_dir,C.RUNTIME_ARTIFACT,'Validation logs local only')]:
        evidence.append(_exists_dir(root, rel, cat, title))
    items=[]
    for ev in evidence:
        p=Path(ev.path)
        if p.is_file() and p.stat().st_size < 500_000:
            items.extend(scan_ledger_text_for_forbidden_markers(p.read_text(encoding='utf-8', errors='replace'), p))
    return evidence, items
