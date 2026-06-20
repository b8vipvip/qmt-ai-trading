from __future__ import annotations
import json
from pathlib import Path
from .models import *
from .collector import collect_live_gray_final_approval_evidence
from .formatters import *

def build_default_live_gray_final_approval_config(**kwargs):
    cfg=LiveGrayFinalApprovalConfig()
    for k,v in kwargs.items(): setattr(cfg,k,v)
    return cfg
def _cap():
    names=['总资金上限','单笔上限','单日上限','单标的上限','组合暴露上限','现金保留比例','最大持仓数','最大下单次数','人工签字状态','不代表实盘授权声明','ETF 白名单人工确认']
    return [CapitalPositionApprovalItem(n) for n in names]
def _risk():
    names=['Risk Gate 不可绕过','Human Approval 不可绕过','不自动 approve','RiskDecision 必须 allowed=True','Approval 必须显式 APPROVED','未批准不得进入 paper/live','UI 未来也不能绕过 Risk Gate / Human Approval','未来真实执行仍需单独审批','Paper Trading / dry-run 证据复核','日志 / 复盘要求审批表']
    return [RiskHumanApprovalItem(n) for n in names]
def _rollback():
    names=['数据质量异常回滚','Risk Gate 异常回滚','Human Approval 缺失回滚','单日亏损触发熔断','总回撤触发熔断','连续错误触发熔断','通知失败时处理','日志缺失时处理','人工暂停流程','恢复前复核流程']
    return [RollbackCircuitApprovalItem(n,n,'默认只读说明：停止推进，保留材料，人工复核；不自动执行交易或通知。') for n in names]
def _signoff():
    roles=['策略负责人签字','风控负责人签字','运行负责人签字','数据负责人签字','最终授权人签字','确认 Stage58 不代表实盘授权','确认 Stage59 仍不得直接实盘','确认不调用 xttrader','确认不真实下单','确认不查询真实账户','确认不真实通知']
    return [FinalSignoffItem(r) for r in roles]
def _seal():
    names=['审批包锁定','配置摘要锁定','风控规则摘要锁定','ETF 白名单锁定','回滚 / 熔断计划锁定','最终签字状态复核','不调用 xttrader','不真实下单','不查询真实账户','不真实通知','下一阶段仍不自动实盘']
    return [NextReadOnlySealPlanItem(n) for n in names]
def _checklist():
    names=['Stage57 灰度候选计划读取状态','Stage56 真实缓存质量复核读取状态','Stage55 QMT dry-run 校准读取状态','资金上限人工确认','单笔上限人工确认','单日上限人工确认','ETF 白名单人工确认','最大持仓数人工确认','单标的上限人工确认','组合暴露上限人工确认','现金保留比例人工确认','单日亏损阈值人工确认','最大回撤阈值人工确认','最大下单次数人工确认','冷却期人工确认','Risk Gate 规则复核','Human Approval 流程复核','Paper Trading / dry-run 证据复核','回滚 / 熔断计划复核','日志 / 复盘要求复核','最终签字清单','下一阶段灰度前只读封版计划']
    return [FinalApprovalChecklistItem(n) for n in names]
def run_live_gray_final_approval(cfg):
    ev=collect_live_gray_final_approval_evidence(cfg); block=[]; warn=[]
    for e in ev:
        if e.severity==LiveGrayFinalApprovalSeverity.CRITICAL: block.append(e.summary)
        elif e.severity==LiveGrayFinalApprovalSeverity.WARN: warn.append(e.summary)
    s57=next((e for e in ev if e.category==LiveGrayFinalApprovalCategory.STAGE57_GRAY_CANDIDATE and e.metadata.get('decision') is not None), None)
    if block: dec=LiveGrayFinalApprovalDecision.NO_GO
    elif s57 and s57.metadata.get('decision')=='READY_FOR_GRAY_CANDIDATE_REVIEW' and int(s57.metadata.get('critical') or 0)==0: dec=LiveGrayFinalApprovalDecision.READY_FOR_FINAL_APPROVAL_REVIEW
    else: dec=LiveGrayFinalApprovalDecision.NEED_MORE_EVIDENCE
    return LiveGrayFinalApprovalReport(decision=dec,evidence=ev,checklist_items=_checklist(),capital_position_items=_cap(),risk_human_items=_risk(),rollback_circuit_items=_rollback(),signoff_items=_signoff(),next_seal_plan_items=_seal(),blocking_reasons=block,warnings=warn,summary=to_plain(cfg))
def _save(md,j,mp,jp): Path(mp).parent.mkdir(parents=True,exist_ok=True); Path(jp).parent.mkdir(parents=True,exist_ok=True); Path(mp).write_text(md,encoding='utf-8'); Path(jp).write_text(j,encoding='utf-8')
def save_live_gray_final_approval_report(r,o,j): _save(format_live_gray_final_approval_report_markdown(r), format_live_gray_final_approval_report_json(r), o, j)
def load_live_gray_final_approval_report(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def run_capital_position_approval(r): return CapitalPositionApprovalReport(r.capital_position_items,r.decision)
def save_capital_position_approval_report(r,o,j): _save(format_capital_position_approval_report_markdown(r), format_simple_json(r), o, j)
def run_risk_human_approval_review(r): return RiskHumanApprovalReviewReport(r.risk_human_items,r.decision)
def save_risk_human_approval_review_report(r,o,j): _save(format_risk_human_approval_review_report_markdown(r), format_simple_json(r), o, j)
def run_rollback_circuit_approval(r): return RollbackCircuitApprovalReport(r.rollback_circuit_items,r.decision)
def save_rollback_circuit_approval_report(r,o,j): _save(format_rollback_circuit_approval_report_markdown(r), format_simple_json(r), o, j)
def run_final_signoff_checklist(r): return FinalSignoffChecklistReport(r.signoff_items,r.decision)
def save_final_signoff_checklist_report(r,o,j): _save(format_final_signoff_checklist_report_markdown(r), format_simple_json(r), o, j)
def run_next_readonly_seal_plan(r): return NextReadOnlySealPlanReport(r.next_seal_plan_items,r.decision)
def save_next_readonly_seal_plan_report(r,o,j): _save(format_next_readonly_seal_plan_report_markdown(r), format_simple_json(r), o, j)
