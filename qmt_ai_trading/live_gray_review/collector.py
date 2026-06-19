from __future__ import annotations
import json
from pathlib import Path
from .models import LiveGrayReviewCategory as C, LiveGrayReviewConfig, LiveGrayReviewEvidence, LiveGrayReviewSeverity as Sev, LiveGrayReviewStatus as S
from .safety import scan_review_text_for_forbidden_markers

def _ev(i,cat,status,sev,path,title,summary,**md): return LiveGrayReviewEvidence(i,cat,status,sev,str(path),title,summary,md)
def _read_json(path: Path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: return {"_error": str(exc)}
def _critical_count(data):
    s=data.get('summary') or {}; return int(s.get('critical') or s.get('critical_count') or 0)

def collect_live_gray_review_evidence(config: LiveGrayReviewConfig):
    root=Path(config.repo_root); evidence=[]; items=[]
    final_dir=root/config.final_authorization_dir
    evidence.append(_ev('stage42-stage39-final-dir',C.STAGE39_FINAL_AUTHORIZATION,S.PASS if final_dir.exists() else S.SKIPPED,Sev.INFO if final_dir.exists() else Sev.WARN,final_dir,'Stage39 final authorization directory','Evidence directory exists.' if final_dir.exists() else 'Stage39 final authorization evidence missing.'))
    red_dir=root/config.redline_review_dir; red_json=red_dir/'redline_review.json'; red_md=red_dir/'redline_review.md'
    if red_json.exists():
        data=_read_json(red_json); decision=data.get('decision'); crit=_critical_count(data)
        sev,status=(Sev.CRITICAL,S.FAIL) if decision=='BLOCKED' or crit>0 else ((Sev.INFO,S.PASS) if crit==0 else (Sev.WARN,S.WARN))
        evidence.append(_ev('stage42-stage40-redline-json',C.STAGE40_REDLINE_REVIEW,status,sev,red_json,'Stage40 redline JSON',f'Stage40 redline decision={decision}; critical={crit}.',decision=decision,critical=crit))
    else: evidence.append(_ev('stage42-stage40-redline-json-missing',C.STAGE40_REDLINE_REVIEW,S.SKIPPED,Sev.WARN,red_json,'Stage40 redline JSON','redline_review.json is missing.'))
    if red_md.exists(): evidence.append(_ev('stage42-stage40-redline-md',C.STAGE40_REDLINE_REVIEW,S.PASS,Sev.INFO,red_md,'Stage40 redline Markdown','redline_review.md exists.'))
    led_dir=root/config.ledger_dir; led_json=led_dir/'live_gray_ledger.json'; led_md=led_dir/'live_gray_ledger.md'
    if led_json.exists():
        data=_read_json(led_json); decision=data.get('decision'); crit=_critical_count(data)
        sev,status=(Sev.CRITICAL,S.FAIL) if decision=='BLOCKED' or crit>0 else ((Sev.WARN,S.WARN) if decision=='NEED_MORE_EVIDENCE' else (Sev.INFO,S.PASS))
        evidence.append(_ev('stage42-stage41-ledger-json',C.STAGE41_LEDGER,status,sev,led_json,'Stage41 live gray ledger JSON',f'Stage41 ledger decision={decision}; critical={crit}.',decision=decision,critical=crit))
    else: evidence.append(_ev('stage42-stage41-ledger-json-missing',C.STAGE41_LEDGER,S.SKIPPED,Sev.WARN,led_json,'Stage41 live gray ledger JSON','live_gray_ledger.json is missing; package can be generated but needs evidence.'))
    if led_md.exists(): evidence.append(_ev('stage42-stage41-ledger-md',C.STAGE41_LEDGER,S.PASS,Sev.INFO,led_md,'Stage41 live gray ledger Markdown','live_gray_ledger.md exists.'))
    val=root/config.validation_logs_dir
    evidence.append(_ev('stage42-validation-logs',C.RUNTIME_ARTIFACT,S.PASS if val.exists() else S.SKIPPED,Sev.INFO if val.exists() else Sev.WARN,val,'Validation logs local only','validation_logs exists locally and remains ignored.' if val.exists() else 'validation_logs is absent; acceptable before local validation.'))
    for ev in evidence:
        p=Path(ev.path)
        if p.is_file() and p.stat().st_size < 500_000:
            items.extend(scan_review_text_for_forbidden_markers(p.read_text(encoding='utf-8', errors='replace'), p))
    return evidence,items
