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

def _evidence(root:Path,path:Path,cat,title):
    rel=str(path.relative_to(root)) if path.exists() and path.is_relative_to(root) else str(path)
    if not path.exists():
        return LiveFinalArchiveEvidence(category=cat,status=LiveFinalArchiveStatus.SKIPPED,severity=LiveFinalArchiveSeverity.WARN,path=rel,title=title,summary=f'{title} 缺失；Stage50 继续生成只读封版材料但需要补证。')
    data=_read_json(path) if path.suffix=='.json' else None
    decision=str((data or {}).get('decision',''))
    crit=_critical_count(data)
    sev=LiveFinalArchiveSeverity.CRITICAL if decision=='NO_GO' or crit>0 else LiveFinalArchiveSeverity.INFO
    status=LiveFinalArchiveStatus.FAIL if sev==LiveFinalArchiveSeverity.CRITICAL else LiveFinalArchiveStatus.PASS
    summary=f'{title} 已读取；decision={decision or "N/A"}; critical={crit}; 仅作 Stage50 材料状态复核，不代表实盘授权。'
    return LiveFinalArchiveEvidence(category=cat,status=status,severity=sev,path=rel,title=title,summary=summary,decision=decision,metadata={'critical':crit})

def collect_live_final_archive_evidence(config: LiveFinalArchiveConfig):
    root=Path(config.repo_root)
    paths=[
        (root/config.consistency_dir/'live_consistency.json',LiveFinalArchiveCategory.STAGE49_CONSISTENCY,'Stage49 consistency JSON'),
        (root/config.consistency_dir/'live_consistency.md',LiveFinalArchiveCategory.STAGE49_CONSISTENCY,'Stage49 consistency Markdown'),
        (root/config.consistency_dir/'material_consistency.json',LiveFinalArchiveCategory.MATERIAL_SEAL,'Stage49 material consistency JSON'),
        (root/config.consistency_dir/'material_consistency.md',LiveFinalArchiveCategory.MATERIAL_SEAL,'Stage49 material consistency Markdown'),
        (root/config.consistency_dir/'human_recheck.json',LiveFinalArchiveCategory.HUMAN_CLOSURE,'Stage49 human recheck JSON'),
        (root/config.consistency_dir/'human_recheck.md',LiveFinalArchiveCategory.HUMAN_CLOSURE,'Stage49 human recheck Markdown'),
        (root/config.consistency_dir/'next_gray_check_plan.json',LiveFinalArchiveCategory.NEXT_READONLY_CHECK,'Stage49 next gray check JSON'),
        (root/config.consistency_dir/'next_gray_check_plan.md',LiveFinalArchiveCategory.NEXT_READONLY_CHECK,'Stage49 next gray check Markdown'),
        (root/config.archive_dir/'live_archive.json',LiveFinalArchiveCategory.STAGE48_ARCHIVE,'Stage48 archive JSON'),
        (root/config.final_review_dir/'live_final_review.json',LiveFinalArchiveCategory.STAGE47_FINAL_REVIEW,'Stage47 final review JSON'),
        (root/config.signoff_dir/'live_signoff.json',LiveFinalArchiveCategory.STAGE46_SIGNOFF,'Stage46 signoff JSON'),
        (root/config.validation_logs_dir,LiveFinalArchiveCategory.RUNTIME_ARTIFACT,'validation_logs runtime directory'),
        (root/'.gitignore',LiveFinalArchiveCategory.SENSITIVE_FILE,'.gitignore ignore rules'),
    ]
    return [_evidence(root,p,c,t) for p,c,t in paths]
