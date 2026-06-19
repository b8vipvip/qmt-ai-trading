from __future__ import annotations
import json
from pathlib import Path
from .models import *

def _read_json(p:Path):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return None

def _critical_count(data):
    if not isinstance(data,dict): return 0
    s=data.get('summary') or {}
    c=s.get('critical',0)
    if isinstance(c,int): return c
    return 0

def _evidence(root:Path,path:Path,cat,title):
    rel=str(path.relative_to(root)) if path.exists() else str(path)
    if not path.exists():
        return LiveConsistencyEvidence(category=cat,status=LiveConsistencyStatus.SKIPPED,severity=LiveConsistencySeverity.WARN,path=rel,title=title,summary=f'{title} 缺失；Stage49 继续生成只读复核材料但需要补证。')
    data=_read_json(path) if path.suffix=='.json' else None
    decision=str((data or {}).get('decision',''))
    crit=_critical_count(data)
    sev=LiveConsistencySeverity.CRITICAL if decision=='NO_GO' or crit>0 else LiveConsistencySeverity.INFO
    status=LiveConsistencyStatus.FAIL if sev==LiveConsistencySeverity.CRITICAL else LiveConsistencyStatus.PASS
    summary=f'{title} 已读取；decision={decision or "N/A"}; critical={crit}; 仅作材料状态复核，不代表实盘授权。'
    return LiveConsistencyEvidence(category=cat,status=status,severity=sev,path=rel,title=title,summary=summary,decision=decision,metadata={'critical':crit})

def collect_live_consistency_evidence(config:LiveConsistencyConfig):
    root=Path(config.repo_root)
    paths=[
        (root/config.archive_dir/'live_archive.json',LiveConsistencyCategory.STAGE48_ARCHIVE,'Stage48 archive JSON'),
        (root/config.archive_dir/'live_archive.md',LiveConsistencyCategory.STAGE48_ARCHIVE,'Stage48 archive Markdown'),
        (root/config.archive_dir/'evidence_remediation_plan.json',LiveConsistencyCategory.REMEDIATION_REVIEW,'Stage48 remediation JSON'),
        (root/config.archive_dir/'human_verification_summary.json',LiveConsistencyCategory.HUMAN_RECHECK,'Stage48 human verification JSON'),
        (root/config.archive_dir/'next_readonly_check_plan.json',LiveConsistencyCategory.NEXT_GRAY_CHECK,'Stage48 next readonly plan JSON'),
        (root/config.final_review_dir/'live_final_review.json',LiveConsistencyCategory.STAGE47_FINAL_REVIEW,'Stage47 final review JSON'),
        (root/config.signoff_dir/'live_signoff.json',LiveConsistencyCategory.STAGE46_SIGNOFF,'Stage46 signoff JSON'),
        (root/config.runbook_dir/'live_runbook.json',LiveConsistencyCategory.STAGE45_RUNBOOK,'Stage45 runbook JSON'),
        (root/config.validation_logs_dir,LiveConsistencyCategory.RUNTIME_ARTIFACT,'validation_logs runtime directory'),
        (root/'.gitignore',LiveConsistencyCategory.SENSITIVE_FILE,'.gitignore ignore rules'),
    ]
    return [_evidence(root,p,c,t) for p,c,t in paths]
