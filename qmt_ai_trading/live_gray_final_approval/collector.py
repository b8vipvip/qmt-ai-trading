from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .models import *
from .safety import scan_live_gray_final_approval_text_for_forbidden_markers

def _load_json(p: Path) -> dict[str, Any]:
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return {}
def _critical_count(d: dict[str, Any]) -> int:
    if isinstance(d.get('summary'), dict) and 'critical' in d['summary']: return int(d['summary'].get('critical') or 0)
    return sum(1 for e in d.get('evidence',[]) if e.get('severity')=='CRITICAL')
def _e(cat,status,severity,title,summary,path='',metadata=None): return LiveGrayFinalApprovalEvidence(cat,status,severity,title,summary,path,metadata or {})
def collect_live_gray_final_approval_evidence(cfg: LiveGrayFinalApprovalConfig) -> list[LiveGrayFinalApprovalEvidence]:
    root=Path(cfg.repo_root); ev=[]
    stage_specs=[(LiveGrayFinalApprovalCategory.STAGE57_GRAY_CANDIDATE,root/cfg.live_gray_candidate_dir/'live_gray_candidate.json','Stage57 gray candidate','READY_FOR_GRAY_CANDIDATE_REVIEW'),(LiveGrayFinalApprovalCategory.STAGE56_REAL_CACHE_QUALITY,root/cfg.real_cache_quality_dir/'real_cache_quality.json','Stage56 real cache quality','READY_FOR_REAL_CACHE_QUALITY_REVIEW'),(LiveGrayFinalApprovalCategory.STAGE55_QMT_DRYRUN_CALIBRATION,root/cfg.qmt_dryrun_calibration_dir/'qmt_dryrun_calibration.json','Stage55 QMT dry-run calibration','READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW')]
    for cat,p,title,ready in stage_specs:
        if not p.exists(): ev.append(_e(cat,LiveGrayFinalApprovalStatus.UNAVAILABLE,LiveGrayFinalApprovalSeverity.WARN,title,f'{title} JSON 缺失，审批包可生成草案但需要补证据。',str(p),{})); continue
        data=_load_json(p); dec=data.get('decision',''); crit=_critical_count(data); sev=LiveGrayFinalApprovalSeverity.CRITICAL if dec=='NO_GO' or crit>0 else LiveGrayFinalApprovalSeverity.INFO; st=LiveGrayFinalApprovalStatus.FAIL if sev==LiveGrayFinalApprovalSeverity.CRITICAL else LiveGrayFinalApprovalStatus.PASS
        ev.append(_e(cat,st,sev,title,f'{title} decision={dec or "UNKNOWN"} critical={crit}',str(p),{'decision':dec,'critical':crit,'ready_decision':ready}))
    for name,rel,cat in [('Stage57 Markdown',Path(cfg.live_gray_candidate_dir)/'live_gray_candidate.md',LiveGrayFinalApprovalCategory.STAGE57_GRAY_CANDIDATE),('Stage57 gray risk limits',Path(cfg.live_gray_candidate_dir)/'gray_risk_limits.json',LiveGrayFinalApprovalCategory.CAPITAL_APPROVAL),('Stage57 approval checklist',Path(cfg.live_gray_candidate_dir)/'gray_approval_checklist.json',LiveGrayFinalApprovalCategory.HUMAN_APPROVAL_FLOW),('Stage57 rollback circuit breaker',Path(cfg.live_gray_candidate_dir)/'gray_rollback_circuit_breaker.json',LiveGrayFinalApprovalCategory.ROLLBACK_APPROVAL),('Stage57 next package plan',Path(cfg.live_gray_candidate_dir)/'next_gray_approval_package_plan.json',LiveGrayFinalApprovalCategory.FINAL_SIGNOFF)]:
        p=root/rel
        ev.append(_e(cat, LiveGrayFinalApprovalStatus.PASS if p.exists() else LiveGrayFinalApprovalStatus.UNAVAILABLE, LiveGrayFinalApprovalSeverity.INFO if p.exists() else LiveGrayFinalApprovalSeverity.WARN, name, f'{name} '+('已读取。' if p.exists() else '缺失，需要补证据。'), str(p)))
    roadmap=root/cfg.roadmap_path; required=['完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）','Stage61：API Gateway 基础层','Stage75：本地控制台封版 / 可选桌面化','UI 不直接访问 QMT','UI 不能绕过 Risk Gate','UI 不能绕过 Human Approval','UI 不能自动 approve']
    txt=roadmap.read_text(encoding='utf-8',errors='ignore') if roadmap.exists() else ''
    missing=[x for x in required if x not in txt]
    ev.append(_e(LiveGrayFinalApprovalCategory.ROADMAP_STAGE_PLAN, LiveGrayFinalApprovalStatus.FAIL if missing else LiveGrayFinalApprovalStatus.PASS, LiveGrayFinalApprovalSeverity.CRITICAL if missing else LiveGrayFinalApprovalSeverity.INFO, 'Roadmap Stage1-75 / UI plan', '缺失: '+', '.join(missing) if missing else '完整 Stage1-75 工程阶段计划和 Stage61-75 UI 产品化路线已保留。', str(roadmap), {'missing':missing}))
    for rel in [cfg.live_gray_candidate_dir, cfg.real_cache_quality_dir, cfg.qmt_dryrun_calibration_dir, 'docs']:
        p=root/rel
        if p.exists():
            for fp in ([p] if p.is_file() else list(p.rglob('*.md'))+list(p.rglob('*.json'))):
                for f in scan_live_gray_final_approval_text_for_forbidden_markers(fp.read_text(encoding='utf-8',errors='ignore'), str(fp)):
                    ev.append(_e(LiveGrayFinalApprovalCategory.QMT_BOUNDARY, LiveGrayFinalApprovalStatus.WARN if f['severity']=='WARN' else LiveGrayFinalApprovalStatus.FAIL, LiveGrayFinalApprovalSeverity(f['severity']), 'Forbidden marker scan', f"marker={f['marker']} context={f['context']}", str(fp)))
    return ev
