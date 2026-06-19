from __future__ import annotations
import json
from pathlib import Path

def _safe_relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)

from .models import *
ROADMAP_KEYS=['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']
def _decision(obj):
    if not isinstance(obj,dict): return ''
    return str(obj.get('decision') or obj.get('summary',{}).get('decision') or '')
def _critical(obj):
    if not isinstance(obj,dict): return 0
    s=obj.get('summary') if isinstance(obj.get('summary'),dict) else {}
    return int(s.get('critical') or s.get('critical_count') or len(obj.get('blocking_reasons') or []))
def _read_json(path:Path):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except Exception: return None
def _evidence(root:Path,path:Path,cat,title):
    rel=_safe_relative_path(path, root)
    if not path.exists():
        return LiveGapClearanceEvidence(category=cat,status=LiveGapClearanceStatus.SKIPPED,severity=LiveGapClearanceSeverity.WARN,path=rel,title=title,summary=f'{title} 缺失，记录为补证项；Stage54 不崩溃且不授权实盘。')
    obj=_read_json(path) if path.suffix.lower()=='.json' else None; dec=_decision(obj); crit=_critical(obj)
    sev=LiveGapClearanceSeverity.CRITICAL if dec=='NO_GO' or crit>0 else LiveGapClearanceSeverity.INFO
    st=LiveGapClearanceStatus.FAIL if sev==LiveGapClearanceSeverity.CRITICAL else LiveGapClearanceStatus.PASS
    return LiveGapClearanceEvidence(category=cat,status=st,severity=sev,path=rel,title=title,summary=f'{title} 已读取；decision={dec or "N/A"}; critical={crit}; 仅用于材料复核，不代表实盘授权。',decision=dec,metadata={'critical':crit})
def _roadmap(root:Path,path:Path):
    rel=_safe_relative_path(path, root)
    if not path.exists(): missing=ROADMAP_KEYS
    else:
        txt=path.read_text(encoding='utf-8'); missing=[k for k in ROADMAP_KEYS if k not in txt]
    sev=LiveGapClearanceSeverity.CRITICAL if missing else LiveGapClearanceSeverity.INFO; st=LiveGapClearanceStatus.FAIL if missing else LiveGapClearanceStatus.PASS
    summary='roadmap 保留完整 Stage1-75 工程计划与 Stage61-75 UI 产品化路线。' if not missing else 'roadmap 缺少关键文本: '+', '.join(missing)
    return [LiveGapClearanceEvidence(category=LiveGapClearanceCategory.ROADMAP_STAGE_PLAN,status=st,severity=sev,path=rel,title='Roadmap Stage1-75 plan',summary=summary,metadata={'missing':missing}),LiveGapClearanceEvidence(category=LiveGapClearanceCategory.UI_PRODUCTIZATION_PLAN,status=st,severity=sev,path=rel,title='Roadmap UI productization plan',summary=summary,metadata={'missing':missing})]
def collect_live_gap_clearance_evidence(config:LiveGapClearanceConfig):
    root=Path(config.repo_root)
    paths=[(root/config.archive_verification_dir/'live_archive_verification.json',LiveGapClearanceCategory.STAGE53_ARCHIVE_VERIFICATION,'Stage53 archive verification JSON'),(root/config.archive_verification_dir/'live_archive_verification.md',LiveGapClearanceCategory.STAGE53_ARCHIVE_VERIFICATION,'Stage53 archive verification Markdown'),(root/config.archive_verification_dir/'locked_material_review.json',LiveGapClearanceCategory.STAGE53_ARCHIVE_VERIFICATION,'Stage53 locked material review JSON'),(root/config.archive_verification_dir/'human_closure_recheck.json',LiveGapClearanceCategory.HUMAN_CLOSURE_RECHECK,'Stage53 human closure recheck JSON'),(root/config.archive_verification_dir/'next_readonly_check_plan.json',LiveGapClearanceCategory.NEXT_READONLY_CHECK,'Stage53 next readonly check plan JSON'),(root/config.lock_consistency_dir/'live_lock_consistency.json',LiveGapClearanceCategory.STAGE52_LOCK_CONSISTENCY,'Stage52 lock consistency JSON'),(root/config.archive_lock_dir/'live_archive_lock.json',LiveGapClearanceCategory.STAGE51_ARCHIVE_LOCK,'Stage51 archive lock JSON'),(root/config.final_archive_dir/'live_final_archive.json',LiveGapClearanceCategory.STAGE50_FINAL_ARCHIVE,'Stage50 final archive JSON'),(root/config.validation_logs_dir,LiveGapClearanceCategory.RUNTIME_ARTIFACT,'validation_logs runtime directory'),(root/'.gitignore',LiveGapClearanceCategory.SENSITIVE_FILE,'.gitignore ignore rules')]
    ev=[_evidence(root,p,c,t) for p,c,t in paths]; ev.extend(_roadmap(root,root/config.roadmap_path)); return ev
