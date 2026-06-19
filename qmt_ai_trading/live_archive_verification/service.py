from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_archive_verification_evidence
from .formatters import *
from .models import *
from .safety import assert_stage53_read_only

def build_default_live_archive_verification_config(repo_root: str|Path='.', **kwargs: Any) -> LiveArchiveVerificationConfig:
    cfg=LiveArchiveVerificationConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg

def _items():
    av=['Stage52 lock consistency 读取状态','Stage51 archive lock 读取状态','Stage50 final archive 读取状态','Stage49 consistency 读取状态','最终归档核验材料索引','锁定材料复核边界说明','工程总阶段计划写入 docs 状态','前端 UI 产品化计划写入 docs 状态','运行产物忽略规则复核','本地只读证据路径复核','当前材料状态','不代表实盘授权声明']
    lm=['Stage49 / Stage50 / Stage51 / Stage52 决策一致性','read_only 一致性','dry_run_only 一致性','no_trade_authorization 一致性','live_trading_enabled=false 或 live disabled 说明一致性','no_task_registered 一致性','Risk Gate / Human Approval 边界声明一致性','不调用 xttrader 声明一致性','不真实下单声明一致性','不真实通知声明一致性','未来真实执行仍需单独审批一致性','docs 中完整 75 阶段计划一致性','docs 中 Stage61-75 UI 计划一致性','锁定材料复核不等于实盘授权声明']
    roles=['演练主持人闭环复查','风险负责人闭环复查','运行负责人闭环复查','配置冻结复核人闭环复查','最终授权人闭环复查','工程计划文档复核','UI 产品化路线文档复核']
    plan=['最终只读归档核验','锁定材料复核','人工闭环复查','工程阶段计划复核','UI 产品化计划复核','配置冻结复查','Risk Gate / Human Approval 边界复查','不接实盘','不调用 xttrader','不真实下单','不查询真实账户','不真实通知','不注册真实任务']
    return ([ArchiveVerificationItem(f'archive-verification-{i}',t,summary=f'{t}：只读核验 Stage49-52 证据状态，不代表实盘授权。') for i,t in enumerate(av,1)],
            [LockedMaterialReviewItem(f'locked-material-review-{i}',t,summary=f'{t}：锁定材料复核只核验材料状态；未来真实执行仍需单独审批。') for i,t in enumerate(lm,1)],
            [HumanClosureRecheckItem(f'human-recheck-{i}',r,statement=f'{r}：确认本项仅用于 Stage53 人工闭环复查，不代表实盘授权；未来真实执行仍需单独审批。') for i,r in enumerate(roles,1)],
            [NextReadonlyCheckItem(f'next-readonly-{i}',t,summary=f'下一阶段检查“{t}”；Stage54 仍不接实盘、不自动 approve、不调用 xttrader、不查账户。') for i,t in enumerate(plan,1)])

def _decide(evidence):
    critical=[e for e in evidence if enum_value(e.severity)=='CRITICAL' or enum_value(e.status)=='FAIL']
    if critical: return LiveArchiveVerificationDecision.NO_GO,[e.summary for e in critical]
    stage52=[e for e in evidence if enum_value(e.category)=='STAGE52_LOCK_CONSISTENCY' and e.decision]
    if any(e.decision=='NEED_MORE_EVIDENCE' for e in stage52): return LiveArchiveVerificationDecision.NEED_MORE_EVIDENCE,[]
    if any(e.decision=='READY_FOR_LOCK_CONSISTENCY_REVIEW' for e in stage52): return LiveArchiveVerificationDecision.READY_FOR_ARCHIVE_VERIFICATION_REVIEW,[]
    warn=[e for e in evidence if enum_value(e.severity)=='WARN' or enum_value(e.status) in {'WARN','SKIPPED'}]
    if warn: return LiveArchiveVerificationDecision.NEED_MORE_EVIDENCE,[]
    return LiveArchiveVerificationDecision.NEED_MORE_EVIDENCE,[]

def run_live_archive_verification(config:LiveArchiveVerificationConfig|None=None, **kwargs:Any)->LiveArchiveVerificationReport:
    cfg=config or build_default_live_archive_verification_config(**kwargs); assert_stage53_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization,cfg.live_trading_enabled,cfg.no_task_registered)
    ev=collect_live_archive_verification_evidence(cfg); decision,blocking=_decide(ev); warnings=[e.summary for e in ev if enum_value(e.severity)=='WARN' or enum_value(e.status) in {'WARN','SKIPPED'}]
    archive,locked,human,plan=_items(); summary={'total_evidence':len(ev),'critical':len(blocking),'warnings':len(warnings),'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'ready_for_archive_verification_review_not_trade_authorization':True}
    return LiveArchiveVerificationReport(decision=decision,config=cfg,evidence=ev,archive_verification=archive,locked_material_review=locked,human_closure_recheck=human,next_readonly_check_plan=plan,blocking_reasons=blocking,warnings=warnings,summary=summary)

def save_live_archive_verification_report(r, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_live_archive_verification_report_json(r) if p.suffix.lower()=='.json' else format_live_archive_verification_report_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_live_archive_verification_report_json(r),encoding='utf-8')
    return p
def load_live_archive_verification_report(path): return LiveArchiveVerificationReport(**json.loads(Path(path).read_text(encoding='utf-8')))
def run_locked_material_review(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveArchiveVerificationReport) else run_live_archive_verification(report_or_config or build_default_live_archive_verification_config(**kw)); return LockedMaterialReviewReport(decision=r.decision,items=r.locked_material_review,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_locked_material_review_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_locked_material_review_report_json(r) if p.suffix.lower()=='.json' else format_locked_material_review_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_locked_material_review_report_json(r),encoding='utf-8')
def run_human_closure_recheck(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveArchiveVerificationReport) else run_live_archive_verification(report_or_config or build_default_live_archive_verification_config(**kw)); return HumanClosureRecheckReport(decision=r.decision,items=r.human_closure_recheck,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_human_closure_recheck_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_human_closure_recheck_report_json(r) if p.suffix.lower()=='.json' else format_human_closure_recheck_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_human_closure_recheck_report_json(r),encoding='utf-8')
def run_next_readonly_check(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveArchiveVerificationReport) else run_live_archive_verification(report_or_config or build_default_live_archive_verification_config(**kw)); return NextReadonlyCheckReport(decision=r.decision,items=r.next_readonly_check_plan,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_next_readonly_check_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_next_readonly_check_report_json(r) if p.suffix.lower()=='.json' else format_next_readonly_check_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_next_readonly_check_report_json(r),encoding='utf-8')
