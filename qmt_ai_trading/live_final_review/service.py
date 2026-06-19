from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_final_review_evidence
from .formatters import *
from .models import *
from .safety import assert_stage47_read_only

def build_default_live_final_review_config(repo_root: str|Path='.', **kwargs: Any) -> LiveFinalReviewConfig:
    cfg=LiveFinalReviewConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg
def _summary_items(decision):
    titles=['Stage46 签字封版读取状态','Stage45 运行手册读取状态','Stage44 环境快照读取状态','Stage43 配置封存读取状态','当前材料决策','当前缺口摘要','安全声明','只读边界','Risk Gate / Human Approval 边界','Scheduler preview 边界','未来真实执行仍需单独审批声明']
    return [GoNoGoSummaryItem(item_id=f'summary-{i}',title=t,summary=f'{t} 已纳入 Stage47 最终只读材料汇总；当前材料决策={enum_value(decision)}；不代表实盘授权。',confirmations=['只读材料状态','不调用 xttrader','不查询真实账户','不下单','不真实发送通知','未来真实执行仍需单独审批']) for i,t in enumerate(titles,1)]
def _signatures():
    roles=['演练主持人签字核验','风险负责人签字核验','运行负责人签字核验','配置冻结复核人签字核验','最终授权人签字核验']
    return [SignatureVerificationItem(item_id=f'signature-{i}',role=r,statement=f'{r}确认材料仅用于最终只读 go/no-go 人工复核；不代表实盘授权；未来真实执行仍需单独审批。') for i,r in enumerate(roles,1)]
def _plan():
    titles=['继续只读复核','人工签字核验','缺口补证','配置冻结复查','不接实盘','不调用 xttrader','不真实下单','不查询真实账户','不真实通知','不注册真实任务']
    return [NextReadonlyPlanItem(item_id=f'plan-{i}',title=t,summary=f'Stage48 前继续执行“{t}”的只读检查，不产生任何实盘授权。') for i,t in enumerate(titles,1)]
def _decide(evidence):
    critical=[x for x in evidence if x.severity==LiveFinalReviewSeverity.CRITICAL or x.status==LiveFinalReviewStatus.FAIL]
    if critical: return LiveFinalReviewDecision.NO_GO,[x.summary for x in critical]
    warn=[x for x in evidence if x.severity==LiveFinalReviewSeverity.WARN or x.status in {LiveFinalReviewStatus.WARN,LiveFinalReviewStatus.SKIPPED}]
    if warn: return LiveFinalReviewDecision.NEED_MORE_EVIDENCE,[]
    return LiveFinalReviewDecision.READY_FOR_FINAL_REVIEW,[]
def _gaps(evidence):
    base=[]
    for stage in ['Stage43 NEED_MORE_EVIDENCE','Stage44 NEED_MORE_EVIDENCE','Stage45 NEED_MORE_EVIDENCE','Stage46 NEED_MORE_EVIDENCE']:
        base.append(EvidenceGapItem(item_id=stage.lower().replace(' ','-'),title=stage,summary=f'{stage} 时必须保留为材料缺口，不升级为实盘授权。'))
    base += [EvidenceGapItem(item_id='stage40-redline',title='redline_review_stage40 缺失提示',summary='Stage40 redline review 缺失时需要补齐本地证据。'),EvidenceGapItem(item_id='validation-logs',title='validation_logs 本地运行产物提示',summary='validation_logs/ 是本地验收产物，应忽略且不提交。'),EvidenceGapItem(item_id='runtime-ignore',title='market_data / reports / logs 忽略规则提示',summary='market_data/、reports/、logs/ 均为运行产物或敏感上下文，不应提交。')]
    for e in evidence:
        if e.severity==LiveFinalReviewSeverity.WARN or e.status in {LiveFinalReviewStatus.WARN,LiveFinalReviewStatus.SKIPPED}:
            base.append(EvidenceGapItem(item_id=f'gap-{len(base)+1}',title=e.title or e.path,severity=LiveFinalReviewSeverity.WARN,summary=e.summary))
    return base
def run_live_final_review(config: LiveFinalReviewConfig|None=None, **kwargs: Any) -> LiveFinalReviewReport:
    cfg=config or build_default_live_final_review_config(**kwargs); assert_stage47_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization,cfg.live_trading_enabled)
    evidence=collect_live_final_review_evidence(cfg); decision,blocking=_decide(evidence); warnings=[x.summary for x in evidence if x.severity==LiveFinalReviewSeverity.WARN or x.status in {LiveFinalReviewStatus.WARN,LiveFinalReviewStatus.SKIPPED}]
    summary={'total_evidence':len(evidence),'critical':len(blocking),'warnings':len(warnings),'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'ready_for_final_review_not_trade_authorization':True}
    gaps=_gaps(evidence)
    return LiveFinalReviewReport(decision=decision,config=cfg,evidence=evidence,go_no_go_summary=_summary_items(decision),signature_verification_items=_signatures(),evidence_gaps=gaps,next_readonly_plan=_plan(),blocking_reasons=blocking,warnings=warnings,summary=summary)
def save_live_final_review_report(report, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_live_final_review_report_json(report) if p.suffix.lower()=='.json' else format_live_final_review_report_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_live_final_review_report_json(report),encoding='utf-8')
    return p
def load_live_final_review_report(path): return LiveFinalReviewReport(**json.loads(Path(path).read_text(encoding='utf-8')))
def run_signature_verification(report_or_config=None, **kwargs):
    report=report_or_config if isinstance(report_or_config,LiveFinalReviewReport) else run_live_final_review(report_or_config or build_default_live_final_review_config(**kwargs))
    return SignatureVerificationReport(decision=report.decision,items=report.signature_verification_items,warnings=report.warnings,blocking_reasons=report.blocking_reasons,summary=report.summary)
def save_signature_verification_report(report, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_signature_verification_report_json(report) if p.suffix.lower()=='.json' else format_signature_verification_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_signature_verification_report_json(report),encoding='utf-8')
    return p
def run_evidence_gap_report(report_or_config=None, **kwargs):
    report=report_or_config if isinstance(report_or_config,LiveFinalReviewReport) else run_live_final_review(report_or_config or build_default_live_final_review_config(**kwargs))
    return EvidenceGapReport(decision=report.decision,items=report.evidence_gaps,warnings=report.warnings,blocking_reasons=report.blocking_reasons,summary=report.summary)
def save_evidence_gap_report(report, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_evidence_gap_report_json(report) if p.suffix.lower()=='.json' else format_evidence_gap_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_evidence_gap_report_json(report),encoding='utf-8')
    return p
def run_next_readonly_plan(report_or_config=None, **kwargs):
    report=report_or_config if isinstance(report_or_config,LiveFinalReviewReport) else run_live_final_review(report_or_config or build_default_live_final_review_config(**kwargs))
    return NextReadonlyPlanReport(decision=report.decision,items=report.next_readonly_plan,warnings=report.warnings,blocking_reasons=report.blocking_reasons,summary=report.summary)
def save_next_readonly_plan_report(report, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_next_readonly_plan_report_json(report) if p.suffix.lower()=='.json' else format_next_readonly_plan_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_next_readonly_plan_report_json(report),encoding='utf-8')
    return p
