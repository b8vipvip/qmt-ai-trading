from __future__ import annotations
import json
from pathlib import Path
from .models import *
from .collector import collect_live_gray_readonly_seal_evidence
from .manifest import build_readonly_seal_manifest_items
from .formatters import *
def build_default_live_gray_readonly_seal_config(**kwargs):
    cfg=LiveGrayReadonlySealConfig()
    for k,v in kwargs.items(): setattr(cfg,k,v)
    return cfg
def _locks(): return [MaterialLockItem(x) for x in ['审批包锁定','配置摘要锁定','风控规则摘要锁定','ETF 白名单锁定','回滚 / 熔断计划锁定','最终签字状态复核','只读锁定声明','不代表实盘授权声明']]
def _check(): return [PreRunChecklistItem(x) for x in ['确认 Stage59 不代表实盘授权','确认 Stage60 仍不得直接实盘','确认不调用 xttrader','确认不真实下单','确认不查询真实账户','确认不真实通知','确认 Risk Gate 不可绕过','确认 Human Approval 不可绕过','确认不自动 approve','确认 register 仍为 dry-run preview','确认 material manifest 已生成','确认运行产物不提交']]
def _sign(): return [FinalSignoffRecheckItem(x) for x in ['策略负责人签字状态','风控负责人签字状态','运行负责人签字状态','数据负责人签字状态','最终授权人签字状态','未签字不得进入后续真实执行审批','本阶段不代表实盘授权']]
def _plan(): return [NextPreGrayReviewPlanItem(x) for x in ['只读封版材料复核','运行前 checklist 复核','manifest hash 复核','Risk Gate 最终复核','Human Approval 最终复核','Paper Trading / dry-run 证据最终复核','不调用 xttrader','不真实下单','不查询真实账户','不真实通知','下一阶段仍不自动实盘']]
def run_live_gray_readonly_seal(cfg):
    ev=collect_live_gray_readonly_seal_evidence(cfg); manifest=build_readonly_seal_manifest_items(cfg); block=[]; warn=[]
    for e in ev:
        if e.severity==LiveGrayReadonlySealSeverity.CRITICAL: block.append(e.summary)
        elif e.severity==LiveGrayReadonlySealSeverity.WARN: warn.append(e.summary)
    s58=next((e for e in ev if e.category==LiveGrayReadonlySealCategory.STAGE58_FINAL_APPROVAL and e.metadata.get('decision') is not None),None)
    if block: dec=LiveGrayReadonlySealDecision.NO_GO
    elif s58 and s58.metadata.get('decision')=='READY_FOR_FINAL_APPROVAL_REVIEW' and int(s58.metadata.get('critical') or 0)==0: dec=LiveGrayReadonlySealDecision.READY_FOR_READONLY_SEAL_REVIEW
    elif s58 and s58.metadata.get('decision')=='NEED_MORE_EVIDENCE' and int(s58.metadata.get('critical') or 0)==0: dec=LiveGrayReadonlySealDecision.NEED_MORE_EVIDENCE
    else: dec=LiveGrayReadonlySealDecision.NEED_MORE_EVIDENCE
    return LiveGrayReadonlySealReport(decision=dec,evidence=ev,material_lock_items=_locks(),checklist_items=_check(),manifest_items=manifest,signoff_items=_sign(),next_plan_items=_plan(),blocking_reasons=block,warnings=warn,summary=to_plain(cfg))
def _save(md,j,mp,jp): Path(mp).parent.mkdir(parents=True,exist_ok=True); Path(jp).parent.mkdir(parents=True,exist_ok=True); Path(mp).write_text(md,encoding='utf-8'); Path(jp).write_text(j,encoding='utf-8')
def save_live_gray_readonly_seal_report(r,o,j): _save(format_live_gray_readonly_seal_report_markdown(r),format_live_gray_readonly_seal_report_json(r),o,j)
def load_live_gray_readonly_seal_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def run_material_lock_report(r): return MaterialLockReport(r.material_lock_items,r.decision)
def save_material_lock_report(r,o,j): _save(format_material_lock_report_markdown(r),format_simple_json(r),o,j)
def run_pre_run_checklist(r): return PreRunChecklistReport(r.checklist_items,r.decision)
def save_pre_run_checklist_report(r,o,j): _save(format_pre_run_checklist_report_markdown(r),format_simple_json(r),o,j)
def run_readonly_seal_manifest(r): return ReadonlySealManifestReport(r.manifest_items,r.decision)
def save_readonly_seal_manifest_report(r,o,j): _save(format_readonly_seal_manifest_report_markdown(r),format_simple_json(r),o,j)
def run_final_signoff_recheck(r): return FinalSignoffRecheckReport(r.signoff_items,r.decision)
def save_final_signoff_recheck_report(r,o,j): _save(format_final_signoff_recheck_report_markdown(r),format_simple_json(r),o,j)
def run_next_pre_gray_review_plan(r): return NextPreGrayReviewPlanReport(r.next_plan_items,r.decision)
def save_next_pre_gray_review_plan_report(r,o,j): _save(format_next_pre_gray_review_plan_report_markdown(r),format_simple_json(r),o,j)
