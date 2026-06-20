from __future__ import annotations
import json
from pathlib import Path
from .models import *
from .collector import collect_pre_gray_final_review_evidence
from .go_no_go import generate_go_no_go_draft
from .formatters import *

def build_default_pre_gray_final_review_config(**kwargs):
    cfg=PreGrayFinalReviewConfig()
    for k,v in kwargs.items(): setattr(cfg,k,v)
    return cfg

def _material(): return [MaterialRecheckItem(x) for x in ['Stage59 只读封版材料读取状态','Stage58 最终人工审批包读取状态','Stage57 小资金灰度候选计划读取状态','Stage56 真实缓存质量复核读取状态','Stage55 QMT dry-run 校准读取状态','只读封版材料复核','不代表实盘授权声明']]
def _checklist(): return [PreRunChecklistRecheckItem(x) for x in ['运行前 checklist 复核','manifest hash 复核','Risk Gate 最终复核','Human Approval 最终复核','Paper Trading / dry-run 证据最终复核','register preview 最终复核']]
def _manifest(ev): return [ManifestHashRecheckItem('Stage59 readonly_seal_manifest.json', any(e.category==PreGrayFinalReviewCategory.MANIFEST_HASH_RECHECK and e.metadata.get('exists') for e in ev), any(e.category==PreGrayFinalReviewCategory.MANIFEST_HASH_RECHECK and e.metadata.get('sha256') for e in ev), PreGrayFinalReviewStatus.PASS if any(e.category==PreGrayFinalReviewCategory.MANIFEST_HASH_RECHECK and e.status==PreGrayFinalReviewStatus.PASS for e in ev) else PreGrayFinalReviewStatus.WARN)]
def _riskhuman(): return [RiskHumanFinalRecheckItem('Risk Gate 不可绕过'),RiskHumanFinalRecheckItem('Human Approval 不可绕过'),RiskHumanFinalRecheckItem('不自动 approve')]
def _paper(): return [PaperDryRunEvidenceItem('Paper Trading / dry-run 证据最终复核'),PaperDryRunEvidenceItem('不调用 xttrader / 不真实下单 / 不查询账户')]
def _blockers(ev):
    names=['任一上游阶段 NO_GO','任一 critical > 0','manifest 缺失','hash 缺失','Risk Gate 复核缺失','Human Approval 复核缺失','register preview 非 dry-run','出现 xttrader / 真实下单 / 账户查询','出现自动 approve / 绕过风控','运行产物或敏感文件准备提交']
    active={n:False for n in names}
    active['任一上游阶段 NO_GO']=any(e.metadata.get('decision')=='NO_GO' for e in ev)
    active['任一 critical > 0']=any(int(e.metadata.get('critical') or 0)>0 or e.severity==PreGrayFinalReviewSeverity.CRITICAL for e in ev)
    active['manifest 缺失']=any(e.category==PreGrayFinalReviewCategory.MANIFEST_HASH_RECHECK and not e.metadata.get('exists') for e in ev)
    active['hash 缺失']=any(e.category==PreGrayFinalReviewCategory.MANIFEST_HASH_RECHECK and not e.metadata.get('sha256') for e in ev)
    active['Human Approval 复核缺失']=any(e.category==PreGrayFinalReviewCategory.HUMAN_APPROVAL_FINAL_RECHECK and e.status!=PreGrayFinalReviewStatus.PASS for e in ev)
    active['register preview 非 dry-run']=any(e.category==PreGrayFinalReviewCategory.REGISTER_PREVIEW_RECHECK and e.status!=PreGrayFinalReviewStatus.PASS for e in ev)
    return [NoGoBlockerItem(n,active[n],PreGrayFinalReviewSeverity.CRITICAL if active[n] and n in ('任一上游阶段 NO_GO','任一 critical > 0','出现 xttrader / 真实下单 / 账户查询','出现自动 approve / 绕过风控') else PreGrayFinalReviewSeverity.WARN) for n in names]
def _conditions(ev):
    names=['Stage55-59 均 READY 或可人工复核','critical=0','material manifest 完整','sha256 完整','pre-run checklist 完整','final signoff recheck 完整','Risk Gate 不可绕过','Human Approval 不可绕过','register preview dry-run only/no task registered','不代表实盘授权']
    ready=all((e.metadata.get('decision') not in (None,'NO_GO')) for e in ev if e.category.name.startswith('STAGE') and e.category!=PreGrayFinalReviewCategory.STAGE61_API_GATEWAY_PLAN)
    crit0=not any(e.severity==PreGrayFinalReviewSeverity.CRITICAL or int(e.metadata.get('critical') or 0)>0 for e in ev)
    man=any(e.category==PreGrayFinalReviewCategory.MANIFEST_HASH_RECHECK and e.metadata.get('exists') for e in ev); sha=any(e.category==PreGrayFinalReviewCategory.MANIFEST_HASH_RECHECK and e.metadata.get('sha256') for e in ev)
    ck=any(e.category==PreGrayFinalReviewCategory.PRE_RUN_CHECKLIST_RECHECK and e.status==PreGrayFinalReviewStatus.PASS for e in ev); sig=any(e.category==PreGrayFinalReviewCategory.HUMAN_APPROVAL_FINAL_RECHECK and e.status==PreGrayFinalReviewStatus.PASS for e in ev); dry=any(e.category==PreGrayFinalReviewCategory.REGISTER_PREVIEW_RECHECK and e.status==PreGrayFinalReviewStatus.PASS for e in ev)
    vals=[ready,crit0,man,sha,ck,sig,True,True,dry,True]
    return [GoConditionItem(n,v) for n,v in zip(names,vals)]
def _gonogo_items(dec): return [GoNoGoDraftItem('go/no-go 草案状态',PreGrayFinalReviewStatus.PASS,dec.value),GoNoGoDraftItem('不代表实盘授权',PreGrayFinalReviewStatus.WARN,'GO_DRAFT 不是实盘授权，仍不得自动实盘')]
def _stage61():
    xs=['Stage61 是 API Gateway 基础层','Stage61 进入 Stage61-75 UI 产品化路线','Stage61 仍不允许 UI 直接访问 QMT','Stage61 仍不能绕过 Risk Gate','Stage61 仍不能绕过 Human Approval','Stage61 不自动 approve','Stage61 不接实盘','Stage61 只搭本地 API 边界和只读查询接口','Stage61 不调用 xttrader','Stage61 不真实下单']
    return [Stage61ApiGatewayPlanItem(x) for x in xs]

def run_pre_gray_final_review(cfg):
    ev=collect_pre_gray_final_review_evidence(cfg); blockers=_blockers(ev); conditions=_conditions(ev); gd=generate_go_no_go_draft(ev,blockers)
    block=[e.summary for e in ev if e.severity==PreGrayFinalReviewSeverity.CRITICAL]+[b.name for b in blockers if b.active and b.severity==PreGrayFinalReviewSeverity.CRITICAL]
    warn=[e.summary for e in ev if e.severity==PreGrayFinalReviewSeverity.WARN]+[b.name for b in blockers if b.active and b.severity==PreGrayFinalReviewSeverity.WARN]
    s59=next((e for e in ev if e.category==PreGrayFinalReviewCategory.STAGE59_READONLY_SEAL),None)
    if block: dec=PreGrayFinalReviewDecision.NO_GO
    elif s59 and s59.metadata.get('decision')=='READY_FOR_READONLY_SEAL_REVIEW' and int(s59.metadata.get('critical') or 0)==0 and not warn: dec=PreGrayFinalReviewDecision.READY_FOR_PRE_GRAY_FINAL_REVIEW
    elif s59 and s59.metadata.get('decision')=='READY_FOR_READONLY_SEAL_REVIEW' and int(s59.metadata.get('critical') or 0)==0: dec=PreGrayFinalReviewDecision.READY_FOR_PRE_GRAY_FINAL_REVIEW
    else: dec=PreGrayFinalReviewDecision.NEED_MORE_EVIDENCE
    return PreGrayFinalReviewReport(dec,gd,evidence=ev,material_items=_material(),checklist_items=_checklist(),manifest_items=_manifest(ev),risk_human_items=_riskhuman(),paper_items=_paper(),blockers=blockers,conditions=conditions,gonogo_items=_gonogo_items(gd),stage61_items=_stage61(),blocking_reasons=block,warnings=warn,summary=to_plain(cfg))

def _save(md,j,o,jp): Path(o).parent.mkdir(parents=True,exist_ok=True); Path(jp).parent.mkdir(parents=True,exist_ok=True); Path(o).write_text(md,encoding='utf-8'); Path(jp).write_text(j,encoding='utf-8')
def save_pre_gray_final_review_report(r,o,j): _save(format_pre_gray_final_review_report_markdown(r),format_json(r),o,j)
def load_pre_gray_final_review_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def run_material_recheck(r): return MaterialRecheckReport(r.material_items,r.decision)
def save_material_recheck_report(r,o,j): _save(format_material_recheck_report_markdown(r),format_json(r),o,j)
def run_go_no_go_draft(r): return GoNoGoDraftReport(r.gonogo_items,r.go_no_go_decision)
def save_go_no_go_draft_report(r,o,j): _save(format_go_no_go_draft_report_markdown(r),format_json(r),o,j)
def run_no_go_blocker_report(r): return NoGoBlockerReport(r.blockers,r.decision)
def save_no_go_blocker_report(r,o,j): _save(format_no_go_blocker_report_markdown(r),format_json(r),o,j)
def run_go_condition_report(r): return GoConditionReport(r.conditions,r.decision)
def save_go_condition_report(r,o,j): _save(format_go_condition_report_markdown(r),format_json(r),o,j)
def run_stage61_api_gateway_plan(r): return Stage61ApiGatewayPlanReport(r.stage61_items,r.decision)
def save_stage61_api_gateway_plan_report(r,o,j): _save(format_stage61_api_gateway_plan_report_markdown(r),format_json(r),o,j)
