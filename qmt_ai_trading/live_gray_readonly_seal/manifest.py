from __future__ import annotations
import hashlib
from pathlib import Path
from .models import *
SENSITIVE=('env','token','key','secret')
def _sha(p: Path)->str:
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def build_readonly_seal_manifest_items(cfg: LiveGrayReadonlySealConfig)->list[ReadonlySealManifestItem]:
    root=Path(cfg.repo_root)
    specs=[
        (cfg.live_gray_final_approval_dir,'live_gray_final_approval.json',LiveGrayReadonlySealCategory.STAGE58_FINAL_APPROVAL,True),(cfg.live_gray_final_approval_dir,'live_gray_final_approval.md',LiveGrayReadonlySealCategory.STAGE58_FINAL_APPROVAL,True),(cfg.live_gray_final_approval_dir,'capital_position_approval.json',LiveGrayReadonlySealCategory.APPROVAL_PACKAGE_LOCK,True),(cfg.live_gray_final_approval_dir,'risk_human_approval_review.json',LiveGrayReadonlySealCategory.RISK_RULE_LOCK,True),(cfg.live_gray_final_approval_dir,'rollback_circuit_approval.json',LiveGrayReadonlySealCategory.ROLLBACK_CIRCUIT_LOCK,True),(cfg.live_gray_final_approval_dir,'final_signoff_checklist.json',LiveGrayReadonlySealCategory.FINAL_SIGNOFF_RECHECK,True),(cfg.live_gray_final_approval_dir,'next_readonly_seal_plan.json',LiveGrayReadonlySealCategory.READONLY_SEAL_INDEX,True),
        (cfg.live_gray_candidate_dir,'live_gray_candidate.json',LiveGrayReadonlySealCategory.STAGE57_GRAY_CANDIDATE,True),(cfg.real_cache_quality_dir,'real_cache_quality.json',LiveGrayReadonlySealCategory.STAGE56_REAL_CACHE_QUALITY,True),(cfg.qmt_dryrun_calibration_dir,'qmt_dryrun_calibration.json',LiveGrayReadonlySealCategory.STAGE55_QMT_DRYRUN_CALIBRATION,True),('docs','qmt-ai-trading-project-roadmap.md',LiveGrayReadonlySealCategory.ROADMAP_STAGE_PLAN,True),]
    items=[]
    for d,n,cat,req in specs:
        rel=str(Path(d)/n).replace('\\','/')
        if any(s in rel.lower() for s in SENSITIVE): continue
        p=root/rel; exists=p.exists(); items.append(ReadonlySealManifestItem(rel,exists,p.stat().st_size if exists else 0,_sha(p) if exists else '',cat,req))
    return items
