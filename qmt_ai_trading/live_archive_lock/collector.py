from __future__ import annotations
import json
from pathlib import Path
from .models import *
def _read_json(p: Path):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return None
def _critical_count(data):
    if not isinstance(data, dict): return 0
    s=data.get('summary') or {}; c=s.get('critical',0)
    return c if isinstance(c,int) else 0
def _rel(path: Path, root: Path) -> str:
    try: return str(path.resolve().relative_to(root.resolve()))
    except Exception: return str(path)
def _evidence(root:Path,path:Path,cat,title):
    rel=_rel(path, root)
    if not path.exists():
        return LiveArchiveLockEvidence(category=cat,status=LiveArchiveLockStatus.SKIPPED,severity=LiveArchiveLockSeverity.WARN,path=rel,title=title,summary=f'{title} 缺失；Stage51 继续生成只读材料但需要补证。')
    data=_read_json(path) if path.suffix=='.json' else None
    decision=str((data or {}).get('decision',''))
    crit=_critical_count(data)
    sev=LiveArchiveLockSeverity.CRITICAL if decision=='NO_GO' or crit>0 else LiveArchiveLockSeverity.INFO
    status=LiveArchiveLockStatus.FAIL if sev==LiveArchiveLockSeverity.CRITICAL else LiveArchiveLockStatus.PASS
    summary=f'{title} 已读取；decision={decision or "N/A"}; critical={crit}; 仅作 Stage51 材料状态复核，不代表实盘授权。'
    return LiveArchiveLockEvidence(category=cat,status=status,severity=sev,path=rel,title=title,summary=summary,decision=decision,metadata={'critical':crit})
def collect_live_archive_lock_evidence(config: LiveArchiveLockConfig):
    root=Path(config.repo_root)
    paths=[
        (root/config.final_archive_dir/'live_final_archive.json',LiveArchiveLockCategory.STAGE50_FINAL_ARCHIVE,'Stage50 final archive JSON'),
        (root/config.final_archive_dir/'live_final_archive.md',LiveArchiveLockCategory.STAGE50_FINAL_ARCHIVE,'Stage50 final archive Markdown'),
        (root/config.final_archive_dir/'material_seal.json',LiveArchiveLockCategory.ARCHIVE_LOCK,'Stage50 material seal JSON'),
        (root/config.final_archive_dir/'material_seal.md',LiveArchiveLockCategory.ARCHIVE_LOCK,'Stage50 material seal Markdown'),
        (root/config.final_archive_dir/'human_closure.json',LiveArchiveLockCategory.HUMAN_CLOSURE_RECHECK,'Stage50 human closure JSON'),
        (root/config.final_archive_dir/'human_closure.md',LiveArchiveLockCategory.HUMAN_CLOSURE_RECHECK,'Stage50 human closure Markdown'),
        (root/config.final_archive_dir/'next_readonly_check_plan.json',LiveArchiveLockCategory.NEXT_READONLY_CHECK,'Stage50 next readonly check plan JSON'),
        (root/config.final_archive_dir/'next_readonly_check_plan.md',LiveArchiveLockCategory.NEXT_READONLY_CHECK,'Stage50 next readonly check plan Markdown'),
        (root/config.consistency_dir/'live_consistency.json',LiveArchiveLockCategory.STAGE49_CONSISTENCY,'Stage49 consistency JSON'),
        (root/config.archive_dir/'live_archive.json',LiveArchiveLockCategory.STAGE48_ARCHIVE,'Stage48 archive JSON'),
        (root/config.final_review_dir/'live_final_review.json',LiveArchiveLockCategory.STAGE47_FINAL_REVIEW,'Stage47 final review JSON'),
        (root/config.validation_logs_dir,LiveArchiveLockCategory.RUNTIME_ARTIFACT,'validation_logs runtime directory'),
        (root/'.gitignore',LiveArchiveLockCategory.SENSITIVE_FILE,'.gitignore ignore rules'),]
    return [_evidence(root,p,c,t) for p,c,t in paths]
