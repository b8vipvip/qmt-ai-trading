from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .models import *
from .manifest import build_readonly_seal_manifest_items
from .safety import scan_live_gray_readonly_seal_text_for_forbidden_markers

def _load_json(p: Path)->dict[str,Any]:
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return {}
def _critical_count(d):
    if isinstance(d.get('summary'),dict) and 'critical' in d['summary']: return int(d['summary'].get('critical') or 0)
    return sum(1 for e in d.get('evidence',[]) if e.get('severity')=='CRITICAL')
def _e(cat,st,sev,title,summary,path='',meta=None): return LiveGrayReadonlySealEvidence(cat,st,sev,title,summary,path,meta or {})
def collect_live_gray_readonly_seal_evidence(cfg: LiveGrayReadonlySealConfig)->list[LiveGrayReadonlySealEvidence]:
    root=Path(cfg.repo_root); ev=[]
    specs=[(LiveGrayReadonlySealCategory.STAGE58_FINAL_APPROVAL,root/cfg.live_gray_final_approval_dir/'live_gray_final_approval.json','Stage58 final approval','READY_FOR_FINAL_APPROVAL_REVIEW'),(LiveGrayReadonlySealCategory.STAGE57_GRAY_CANDIDATE,root/cfg.live_gray_candidate_dir/'live_gray_candidate.json','Stage57 gray candidate','READY_FOR_GRAY_CANDIDATE_REVIEW'),(LiveGrayReadonlySealCategory.STAGE56_REAL_CACHE_QUALITY,root/cfg.real_cache_quality_dir/'real_cache_quality.json','Stage56 real cache quality','READY_FOR_REAL_CACHE_QUALITY_REVIEW'),(LiveGrayReadonlySealCategory.STAGE55_QMT_DRYRUN_CALIBRATION,root/cfg.qmt_dryrun_calibration_dir/'qmt_dryrun_calibration.json','Stage55 QMT dry-run calibration','READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW')]
    for cat,p,title,ready in specs:
        if not p.exists(): ev.append(_e(cat,LiveGrayReadonlySealStatus.UNAVAILABLE,LiveGrayReadonlySealSeverity.WARN,title,f'{title} JSON 缺失，只读封版可生成草案但需要补证据。',str(p),{})); continue
        data=_load_json(p); dec=data.get('decision',''); crit=_critical_count(data); sev=LiveGrayReadonlySealSeverity.CRITICAL if dec=='NO_GO' or crit>0 else LiveGrayReadonlySealSeverity.INFO; st=LiveGrayReadonlySealStatus.FAIL if sev==LiveGrayReadonlySealSeverity.CRITICAL else LiveGrayReadonlySealStatus.PASS
        ev.append(_e(cat,st,sev,title,f'{title} decision={dec or "UNKNOWN"} critical={crit}',str(p),{'decision':dec,'critical':crit,'ready_decision':ready}))
    reqs=[('Stage58 Markdown',cfg.live_gray_final_approval_dir,'live_gray_final_approval.md',LiveGrayReadonlySealCategory.APPROVAL_PACKAGE_LOCK),('capital approval',cfg.live_gray_final_approval_dir,'capital_position_approval.json',LiveGrayReadonlySealCategory.CONFIG_SUMMARY_LOCK),('risk approval',cfg.live_gray_final_approval_dir,'risk_human_approval_review.json',LiveGrayReadonlySealCategory.RISK_RULE_LOCK),('rollback approval',cfg.live_gray_final_approval_dir,'rollback_circuit_approval.json',LiveGrayReadonlySealCategory.ROLLBACK_CIRCUIT_LOCK),('final signoff',cfg.live_gray_final_approval_dir,'final_signoff_checklist.json',LiveGrayReadonlySealCategory.FINAL_SIGNOFF_RECHECK),('next plan',cfg.live_gray_final_approval_dir,'next_readonly_seal_plan.json',LiveGrayReadonlySealCategory.READONLY_SEAL_INDEX)]
    for name,d,n,cat in reqs:
        p=root/d/n; ev.append(_e(cat,LiveGrayReadonlySealStatus.PASS if p.exists() else LiveGrayReadonlySealStatus.UNAVAILABLE,LiveGrayReadonlySealSeverity.INFO if p.exists() else LiveGrayReadonlySealSeverity.WARN,name,(name+' 已读取。') if p.exists() else (name+' 缺失，需要补证据。'),str(p)))
    missing_manifest=[i.relative_path for i in build_readonly_seal_manifest_items(cfg) if i.required and not i.exists]
    ev.append(_e(LiveGrayReadonlySealCategory.MATERIAL_MANIFEST,LiveGrayReadonlySealStatus.WARN if missing_manifest else LiveGrayReadonlySealStatus.PASS,LiveGrayReadonlySealSeverity.WARN if missing_manifest else LiveGrayReadonlySealSeverity.INFO,'material manifest / hash 摘要','缺失 required: '+', '.join(missing_manifest) if missing_manifest else 'manifest 条目完整且包含 sha256。','',{'missing':missing_manifest}))
    roadmap=root/cfg.roadmap_path; required=['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']
    txt=roadmap.read_text(encoding='utf-8',errors='ignore') if roadmap.exists() else ''; miss=[x for x in required if x not in txt]
    ev.append(_e(LiveGrayReadonlySealCategory.ROADMAP_STAGE_PLAN,LiveGrayReadonlySealStatus.FAIL if miss else LiveGrayReadonlySealStatus.PASS,LiveGrayReadonlySealSeverity.CRITICAL if miss else LiveGrayReadonlySealSeverity.INFO,'Roadmap Stage1-75 / UI plan','缺失: '+', '.join(miss) if miss else '完整 Stage1-75 工程阶段计划和 Stage61-75 UI 产品化路线已保留。',str(roadmap),{'missing':miss}))
    for rel in [cfg.live_gray_final_approval_dir,cfg.live_gray_candidate_dir,cfg.real_cache_quality_dir,cfg.qmt_dryrun_calibration_dir,'docs']:
        p=root/rel
        if p.exists():
            for fp in ([p] if p.is_file() else list(p.rglob('*.md'))+list(p.rglob('*.json'))):
                for f in scan_live_gray_readonly_seal_text_for_forbidden_markers(fp.read_text(encoding='utf-8',errors='ignore'),str(fp)):
                    ev.append(_e(LiveGrayReadonlySealCategory.QMT_BOUNDARY,LiveGrayReadonlySealStatus.WARN if f['severity']=='WARN' else LiveGrayReadonlySealStatus.FAIL,LiveGrayReadonlySealSeverity(f['severity']),'Forbidden marker scan',f"marker={f['marker']} context={f['context']}",str(fp)))
    return ev
