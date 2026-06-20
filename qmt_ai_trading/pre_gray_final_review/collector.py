from __future__ import annotations
import json
from pathlib import Path
from .models import *
from .safety import scan_pre_gray_final_review_text_for_forbidden_markers

def _read_json(p: Path):
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return None

def _crit(data):
    if not isinstance(data, dict): return 0
    s=data.get('summary') or {}; return int(data.get('critical') or s.get('critical') or s.get('critical_count') or 0)
def _decision(data):
    return data.get('decision') if isinstance(data, dict) else None

def _stage(cfg, cat, rel, title):
    root=Path(cfg.repo_root); p=root/rel; data=_read_json(p); md=p.with_suffix('.md')
    if data is None:
        return PreGrayFinalReviewEvidence(cat,PreGrayFinalReviewStatus.UNAVAILABLE,PreGrayFinalReviewSeverity.WARN,title,'材料缺失，需补充证据',str(p),{})
    d=_decision(data); c=_crit(data); sev=PreGrayFinalReviewSeverity.CRITICAL if d=='NO_GO' or c>0 else PreGrayFinalReviewSeverity.INFO
    st=PreGrayFinalReviewStatus.FAIL if sev==PreGrayFinalReviewSeverity.CRITICAL else PreGrayFinalReviewStatus.PASS
    return PreGrayFinalReviewEvidence(cat,st,sev,title,f'{title} decision={d} critical={c}',str(p),{'decision':d,'critical':c,'markdown_exists':md.exists()})

def collect_pre_gray_final_review_evidence(cfg: PreGrayFinalReviewConfig):
    root=Path(cfg.repo_root); ev=[]
    ev.append(_stage(cfg,PreGrayFinalReviewCategory.STAGE59_READONLY_SEAL,Path(cfg.live_gray_readonly_seal_dir)/'live_gray_readonly_seal.json','Stage59 只读封版读取状态'))
    ev.append(_stage(cfg,PreGrayFinalReviewCategory.STAGE58_FINAL_APPROVAL,Path(cfg.live_gray_final_approval_dir)/'live_gray_final_approval.json','Stage58 最终人工审批包读取状态'))
    ev.append(_stage(cfg,PreGrayFinalReviewCategory.STAGE57_GRAY_CANDIDATE,Path(cfg.live_gray_candidate_dir)/'live_gray_candidate.json','Stage57 小资金灰度候选计划读取状态'))
    ev.append(_stage(cfg,PreGrayFinalReviewCategory.STAGE56_REAL_CACHE_QUALITY,Path(cfg.real_cache_quality_dir)/'real_cache_quality.json','Stage56 真实缓存质量复核读取状态'))
    ev.append(_stage(cfg,PreGrayFinalReviewCategory.STAGE55_QMT_DRYRUN_CALIBRATION,Path(cfg.qmt_dryrun_calibration_dir)/'qmt_dryrun_calibration.json','Stage55 QMT dry-run 校准读取状态'))
    seal= root/Path(cfg.live_gray_readonly_seal_dir)
    manifest=seal/'readonly_seal_manifest.json'; checklist=seal/'pre_run_checklist.json'; signoff=seal/'final_signoff_recheck.json'
    mdata=_read_json(manifest); has_sha='sha256' in (manifest.read_text(encoding='utf-8') if manifest.exists() else '')
    ev.append(PreGrayFinalReviewEvidence(PreGrayFinalReviewCategory.MANIFEST_HASH_RECHECK,PreGrayFinalReviewStatus.PASS if manifest.exists() and has_sha else PreGrayFinalReviewStatus.UNAVAILABLE,PreGrayFinalReviewSeverity.INFO if manifest.exists() and has_sha else PreGrayFinalReviewSeverity.WARN,'manifest hash 复核','manifest 存在且包含 sha256' if manifest.exists() and has_sha else 'manifest 或 sha256 缺失',str(manifest),{'exists':manifest.exists(),'sha256':has_sha}))
    for p,cat,title in [(checklist,PreGrayFinalReviewCategory.PRE_RUN_CHECKLIST_RECHECK,'运行前 checklist 复核'),(signoff,PreGrayFinalReviewCategory.HUMAN_APPROVAL_FINAL_RECHECK,'Human Approval 最终复核')]:
        ev.append(PreGrayFinalReviewEvidence(cat,PreGrayFinalReviewStatus.PASS if p.exists() else PreGrayFinalReviewStatus.UNAVAILABLE,PreGrayFinalReviewSeverity.INFO if p.exists() else PreGrayFinalReviewSeverity.WARN,title,'材料存在' if p.exists() else '材料缺失',str(p),{'exists':p.exists()}))
    combined='\n'.join(f.read_text(encoding='utf-8',errors='ignore') for f in seal.glob('*') if f.is_file())
    dry = all(x in combined for x in ['dry_run_only','no_task_registered']) or all(x in combined for x in ['dry-run','不注册'])
    ev.append(PreGrayFinalReviewEvidence(PreGrayFinalReviewCategory.REGISTER_PREVIEW_RECHECK,PreGrayFinalReviewStatus.PASS if dry else PreGrayFinalReviewStatus.WARN,PreGrayFinalReviewSeverity.INFO if dry else PreGrayFinalReviewSeverity.WARN,'register preview 最终复核','register preview 为 dry-run only/no task registered' if dry else '未发现完整 dry-run/no task registered 证据',str(seal),{'dry_run_only':dry}))
    road=root/cfg.roadmap_path; text=road.read_text(encoding='utf-8') if road.exists() else ''
    keys=['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']
    missing=[k for k in keys if k not in text]
    ev.append(PreGrayFinalReviewEvidence(PreGrayFinalReviewCategory.ROADMAP_STAGE_PLAN,PreGrayFinalReviewStatus.PASS if not missing else PreGrayFinalReviewStatus.FAIL,PreGrayFinalReviewSeverity.INFO if not missing else PreGrayFinalReviewSeverity.CRITICAL,'roadmap Stage1-75 / UI 产品化路线复核','roadmap 关键文本完整' if not missing else 'roadmap 缺失: '+','.join(missing),str(road),{'missing':missing}))
    hits=scan_pre_gray_final_review_text_for_forbidden_markers(combined, str(seal))
    for h in hits:
        if h['severity']==PreGrayFinalReviewSeverity.CRITICAL:
            ev.append(PreGrayFinalReviewEvidence(PreGrayFinalReviewCategory.QMT_BOUNDARY,PreGrayFinalReviewStatus.FAIL,PreGrayFinalReviewSeverity.CRITICAL,'交易边界扫描','发现真实执行禁用标记 '+h['marker'],str(seal),h))
    return ev
