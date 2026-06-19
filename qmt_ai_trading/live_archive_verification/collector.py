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
        return LiveArchiveVerificationEvidence(category=cat,status=LiveArchiveVerificationStatus.SKIPPED,severity=LiveArchiveVerificationSeverity.WARN,path=rel,title=title,summary=f'{title} 缺失；Stage53 继续生成只读材料但需要补证。')
    data=_read_json(path) if path.suffix=='.json' else None
    decision=str((data or {}).get('decision',''))
    crit=_critical_count(data)
    sev=LiveArchiveVerificationSeverity.CRITICAL if decision=='NO_GO' or crit>0 else LiveArchiveVerificationSeverity.INFO
    status=LiveArchiveVerificationStatus.FAIL if sev==LiveArchiveVerificationSeverity.CRITICAL else LiveArchiveVerificationStatus.PASS
    summary=f'{title} 已读取；decision={decision or "N/A"}; critical={crit}; 仅作 Stage53 材料状态复核，不代表实盘授权。'
    return LiveArchiveVerificationEvidence(category=cat,status=status,severity=sev,path=rel,title=title,summary=summary,decision=decision,metadata={'critical':crit})

def _roadmap_evidence(root:Path, path:Path):
    required=['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']
    rel=_rel(path, root)
    if not path.exists():
        return [LiveArchiveVerificationEvidence(category=LiveArchiveVerificationCategory.ROADMAP_STAGE_PLAN,status=LiveArchiveVerificationStatus.FAIL,severity=LiveArchiveVerificationSeverity.CRITICAL,path=rel,title='Roadmap Stage1-75 plan',summary='roadmap 缺失，无法核验本阶段强制工程计划。')]
    text=path.read_text(encoding='utf-8')
    missing=[x for x in required if x not in text]
    sev=LiveArchiveVerificationSeverity.CRITICAL if missing else LiveArchiveVerificationSeverity.INFO
    status=LiveArchiveVerificationStatus.FAIL if missing else LiveArchiveVerificationStatus.PASS
    summary='roadmap 已写入完整 Stage1-75 工程计划与 Stage61-75 UI 产品化路线。' if not missing else 'roadmap 缺少关键文本: '+', '.join(missing)
    return [LiveArchiveVerificationEvidence(category=LiveArchiveVerificationCategory.ROADMAP_STAGE_PLAN,status=status,severity=sev,path=rel,title='Roadmap Stage1-75 plan',summary=summary,metadata={'missing':missing}), LiveArchiveVerificationEvidence(category=LiveArchiveVerificationCategory.UI_PRODUCTIZATION_PLAN,status=status,severity=sev,path=rel,title='Roadmap UI productization plan',summary=summary,metadata={'missing':missing})]

def collect_live_archive_verification_evidence(config: LiveArchiveVerificationConfig):
    root=Path(config.repo_root)
    paths=[
        (root/config.lock_consistency_dir/'live_lock_consistency.json',LiveArchiveVerificationCategory.STAGE52_LOCK_CONSISTENCY,'Stage52 live lock consistency JSON'),
        (root/config.lock_consistency_dir/'live_lock_consistency.md',LiveArchiveVerificationCategory.STAGE52_LOCK_CONSISTENCY,'Stage52 live lock consistency Markdown'),
        (root/config.lock_consistency_dir/'archive_consistency.json',LiveArchiveVerificationCategory.STAGE52_LOCK_CONSISTENCY,'Stage52 archive consistency JSON'),
        (root/config.lock_consistency_dir/'archive_consistency.md',LiveArchiveVerificationCategory.STAGE52_LOCK_CONSISTENCY,'Stage52 archive consistency Markdown'),
        (root/config.lock_consistency_dir/'human_closure_recheck.json',LiveArchiveVerificationCategory.HUMAN_CLOSURE_RECHECK,'Stage52 human closure recheck JSON'),
        (root/config.lock_consistency_dir/'next_readonly_check_plan.json',LiveArchiveVerificationCategory.NEXT_READONLY_CHECK,'Stage52 next readonly check plan JSON'),
        (root/config.archive_lock_dir/'live_archive_lock.json',LiveArchiveVerificationCategory.STAGE51_ARCHIVE_LOCK,'Stage51 archive lock JSON'),
        (root/config.final_archive_dir/'live_final_archive.json',LiveArchiveVerificationCategory.STAGE50_FINAL_ARCHIVE,'Stage50 final archive JSON'),
        (root/config.consistency_dir/'live_consistency.json',LiveArchiveVerificationCategory.STAGE49_CONSISTENCY,'Stage49 consistency JSON'),
        (root/config.validation_logs_dir,LiveArchiveVerificationCategory.RUNTIME_ARTIFACT,'validation_logs runtime directory'),
        (root/'.gitignore',LiveArchiveVerificationCategory.SENSITIVE_FILE,'.gitignore ignore rules'),]
    ev=[_evidence(root,p,c,t) for p,c,t in paths]
    ev.extend(_roadmap_evidence(root, root/config.roadmap_path))
    return ev
