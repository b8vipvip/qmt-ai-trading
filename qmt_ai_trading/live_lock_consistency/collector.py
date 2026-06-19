from __future__ import annotations
import json
from pathlib import Path
from .models import *
def _read_json(p: Path):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return None
def _critical_count(data):
    if not isinstance(data, dict): return 0
    s=data.get('summary') or {}; c=s.get('critical', data.get('critical',0))
    return c if isinstance(c,int) else 0
def _rel(path: Path, root: Path) -> str:
    try: return str(path.resolve().relative_to(root.resolve()))
    except Exception: return str(path)
def _evidence(root:Path,path:Path,cat,title):
    rel=_rel(path, root)
    if not path.exists():
        return LiveLockConsistencyEvidence(category=cat,status=LiveLockConsistencyStatus.SKIPPED,severity=LiveLockConsistencySeverity.WARN,path=rel,title=title,summary=f'{title} 缺失；Stage52 继续生成只读材料但需要补证。')
    data=_read_json(path) if path.suffix=='.json' else None
    decision=str((data or {}).get('decision',''))
    crit=_critical_count(data)
    sev=LiveLockConsistencySeverity.CRITICAL if decision=='NO_GO' or crit>0 else LiveLockConsistencySeverity.INFO
    status=LiveLockConsistencyStatus.FAIL if sev==LiveLockConsistencySeverity.CRITICAL else LiveLockConsistencyStatus.PASS
    summary=f'{title} 已读取；decision={decision or "N/A"}; critical={crit}; 仅作 Stage52 材料状态复核，不代表实盘授权。'
    return LiveLockConsistencyEvidence(category=cat,status=status,severity=sev,path=rel,title=title,summary=summary,decision=decision,metadata={'critical':crit})
def collect_live_lock_consistency_evidence(config: LiveLockConsistencyConfig):
    root=Path(config.repo_root)
    paths=[
        (root/config.archive_lock_dir/'live_archive_lock.json',LiveLockConsistencyCategory.STAGE51_ARCHIVE_LOCK,'Stage51 archive lock JSON'),
        (root/config.archive_lock_dir/'live_archive_lock.md',LiveLockConsistencyCategory.STAGE51_ARCHIVE_LOCK,'Stage51 archive lock Markdown'),
        (root/config.archive_lock_dir/'archive_lock.json',LiveLockConsistencyCategory.STAGE51_ARCHIVE_LOCK,'Stage51 archive lock package JSON'),
        (root/config.archive_lock_dir/'archive_lock.md',LiveLockConsistencyCategory.STAGE51_ARCHIVE_LOCK,'Stage51 archive lock package Markdown'),
        (root/config.archive_lock_dir/'human_closure_recheck.json',LiveLockConsistencyCategory.HUMAN_CLOSURE_RECHECK,'Stage51 human closure recheck JSON'),
        (root/config.archive_lock_dir/'human_closure_recheck.md',LiveLockConsistencyCategory.HUMAN_CLOSURE_RECHECK,'Stage51 human closure recheck Markdown'),
        (root/config.archive_lock_dir/'next_readonly_check_plan.json',LiveLockConsistencyCategory.NEXT_READONLY_CHECK,'Stage51 next readonly check plan JSON'),
        (root/config.archive_lock_dir/'next_readonly_check_plan.md',LiveLockConsistencyCategory.NEXT_READONLY_CHECK,'Stage51 next readonly check plan Markdown'),
        (root/config.final_archive_dir/'live_final_archive.json',LiveLockConsistencyCategory.STAGE50_FINAL_ARCHIVE,'Stage50 final archive JSON'),
        (root/config.consistency_dir/'live_consistency.json',LiveLockConsistencyCategory.STAGE49_CONSISTENCY,'Stage49 consistency JSON'),
        (root/config.archive_dir/'live_archive.json',LiveLockConsistencyCategory.STAGE48_ARCHIVE,'Stage48 archive JSON'),
        (root/config.validation_logs_dir,LiveLockConsistencyCategory.RUNTIME_ARTIFACT,'validation_logs runtime directory'),
        (root/'.gitignore',LiveLockConsistencyCategory.SENSITIVE_FILE,'.gitignore ignore rules'),]
    return [_evidence(root,p,c,t) for p,c,t in paths]
