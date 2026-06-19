from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_gap_clearance_evidence
from .formatters import *
from .models import *
from .safety import assert_stage54_read_only

def build_default_live_gap_clearance_config(repo_root: str|Path='.', **kwargs: Any) -> LiveGapClearanceConfig:
    cfg=LiveGapClearanceConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg

def _items():
    gap=['Stage53 archive verification 读取状态','Stage52 lock consistency 读取状态','Stage51 archive lock 读取状态','Stage50 final archive 读取状态','历史 NEED_MORE_EVIDENCE 项汇总','历史 warnings 项汇总','必须清零项','可保留说明项','补证项责任说明','roadmap Stage1-75 / UI 产品化路线复核','运行产物忽略规则复核','当前材料状态','不代表实盘授权声明']
    rem=['Stage50 / Stage51 / Stage52 / Stage53 决策一致性','read_only 一致性','dry_run_only 一致性','no_trade_authorization 一致性','live_trading_enabled=false 或 live disabled 说明一致性','no_task_registered 一致性','Risk Gate / Human Approval 边界声明一致性','不调用 xttrader 声明一致性','不真实下单声明一致性','不真实通知声明一致性','未来真实执行仍需单独审批一致性','docs 中完整 75 阶段计划一致性','docs 中 Stage61-75 UI 计划一致性','灰度前缺口清零计划不等于实盘授权声明']
    roles=['演练主持人闭环复查','风险负责人闭环复查','运行负责人闭环复查','配置冻结复核人闭环复查','最终授权人闭环复查','工程计划文档复核','UI 产品化路线文档复核','缺口清零计划复核']
    plan=['灰度前最终缺口清零计划','补证项复核','人工闭环复查','工程阶段计划复核','UI 产品化计划复核','QMT 实机 dry-run 环境校准准备','配置冻结复查','Risk Gate / Human Approval 边界复查','不接实盘','不调用 xttrader','不真实下单','不查询真实账户','不真实通知','不注册真实任务']
    return ([GapClearanceItem(f'gap-clearance-{i}',t,summary=f'{t}：只读汇总 Stage50-53 证据状态，不代表实盘授权。') for i,t in enumerate(gap,1)],
            [EvidenceRemediationItem(f'evidence-remediation-{i}',t,summary=f'{t}：补证项复核只核验材料状态；未来真实执行仍需单独审批。') for i,t in enumerate(rem,1)],
            [HumanClosureRecheckItem(f'human-recheck-{i}',r,statement=f'{r}：确认本项仅用于 Stage54 人工闭环复查，不代表实盘授权；未来真实执行仍需单独审批。') for i,r in enumerate(roles,1)],
            [NextReadonlyCheckItem(f'next-readonly-{i}',t,summary=f'下一阶段检查“{t}”；Stage55 仍不接实盘、不调用 xttrader、不查账户、不下单、不真实通知、不注册真实任务。') for i,t in enumerate(plan,1)])

def _decide(evidence):
    critical=[e for e in evidence if enum_value(e.severity)=='CRITICAL' or enum_value(e.status)=='FAIL']
    if critical: return LiveGapClearanceDecision.NO_GO,[e.summary for e in critical]
    stage53=[e for e in evidence if enum_value(e.category)=='STAGE53_ARCHIVE_VERIFICATION' and e.decision]
    if any(e.decision=='NO_GO' for e in stage53): return LiveGapClearanceDecision.NO_GO,[e.summary for e in stage53 if e.decision=='NO_GO']
    if any(e.decision=='NEED_MORE_EVIDENCE' for e in stage53): return LiveGapClearanceDecision.NEED_MORE_EVIDENCE,[]
    if any(e.decision=='READY_FOR_ARCHIVE_VERIFICATION_REVIEW' for e in stage53): return LiveGapClearanceDecision.READY_FOR_GAP_CLEARANCE_REVIEW,[]
    warn=[e for e in evidence if enum_value(e.severity)=='WARN' or enum_value(e.status) in {'WARN','SKIPPED'}]
    return (LiveGapClearanceDecision.NEED_MORE_EVIDENCE,[]) if warn else (LiveGapClearanceDecision.NEED_MORE_EVIDENCE,[])

def run_live_gap_clearance(config:LiveGapClearanceConfig|None=None, **kwargs:Any)->LiveGapClearanceReport:
    cfg=config or build_default_live_gap_clearance_config(**kwargs); assert_stage54_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization,cfg.live_trading_enabled,cfg.no_task_registered)
    ev=collect_live_gap_clearance_evidence(cfg); decision,blocking=_decide(ev); warnings=[e.summary for e in ev if enum_value(e.severity)=='WARN' or enum_value(e.status) in {'WARN','SKIPPED'}]
    gap,rem,human,plan=_items(); summary={'total_evidence':len(ev),'critical':len(blocking),'warnings':len(warnings),'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'ready_for_gap_clearance_review_not_trade_authorization':True}
    return LiveGapClearanceReport(decision=decision,config=cfg,evidence=ev,gap_clearance=gap,evidence_remediation=rem,human_closure_recheck=human,next_readonly_check_plan=plan,blocking_reasons=blocking,warnings=warnings,summary=summary)

def save_live_gap_clearance_report(r, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_live_gap_clearance_report_json(r) if p.suffix.lower()=='.json' else format_live_gap_clearance_report_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_live_gap_clearance_report_json(r),encoding='utf-8')
    return p
def load_live_gap_clearance_report(path): return LiveGapClearanceReport(**json.loads(Path(path).read_text(encoding='utf-8')))
def run_evidence_remediation(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveGapClearanceReport) else run_live_gap_clearance(report_or_config or build_default_live_gap_clearance_config(**kw)); return EvidenceRemediationReport(decision=r.decision,items=r.evidence_remediation,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_evidence_remediation_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_evidence_remediation_report_json(r) if p.suffix.lower()=='.json' else format_evidence_remediation_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_evidence_remediation_report_json(r),encoding='utf-8')
def run_human_closure_recheck(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveGapClearanceReport) else run_live_gap_clearance(report_or_config or build_default_live_gap_clearance_config(**kw)); return HumanClosureRecheckReport(decision=r.decision,items=r.human_closure_recheck,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_human_closure_recheck_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_human_closure_recheck_report_json(r) if p.suffix.lower()=='.json' else format_human_closure_recheck_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_human_closure_recheck_report_json(r),encoding='utf-8')
def run_next_readonly_check(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveGapClearanceReport) else run_live_gap_clearance(report_or_config or build_default_live_gap_clearance_config(**kw)); return NextReadonlyCheckReport(decision=r.decision,items=r.next_readonly_check_plan,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_next_readonly_check_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_next_readonly_check_report_json(r) if p.suffix.lower()=='.json' else format_next_readonly_check_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_next_readonly_check_report_json(r),encoding='utf-8')
