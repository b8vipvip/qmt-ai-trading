from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_consistency_evidence
from .formatters import *
from .models import *
from .safety import assert_stage49_read_only

def build_default_live_consistency_config(repo_root: str|Path='.', **kwargs: Any) -> LiveConsistencyConfig:
    cfg=LiveConsistencyConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg
def _items():
    rem=["Stage48 archive 读取状态","Stage47 final review 读取状态","Stage46 signoff 读取状态","Stage45 runbook 读取状态","缺口补证项复核","本地只读证据路径复核","运行产物忽略规则复核","当前材料状态","下一步人工复核要求","不代表实盘授权声明"]
    mat=["Stage45 / Stage46 / Stage47 / Stage48 决策一致性","read_only 一致性","dry_run_only 一致性","no_trade_authorization 一致性","live_trading_enabled=false 或 live disabled 说明一致性","no_task_registered 一致性","Risk Gate / Human Approval 边界声明一致性","不调用 xttrader 声明一致性","不真实下单声明一致性","不真实通知声明一致性"]
    roles=["演练主持人复查","风险负责人复查","运行负责人复查","配置冻结复核人复查","最终授权人复查"]
    plan=["补证后只读复核","最终材料一致性复查","人工核验复查","配置冻结复查","Risk Gate / Human Approval 边界复查","不接实盘","不调用 xttrader","不真实下单","不查询真实账户","不真实通知","不注册真实任务"]
    return ([RemediationReviewItem(f"remediation-{i}",t,summary=f"{t}：只读复核材料状态，不代表实盘授权。") for i,t in enumerate(rem,1)],
            [MaterialConsistencyItem(f"material-{i}",t,summary=f"{t}：保持 Stage45-48 材料边界一致；READY_FOR_CONSISTENCY_REVIEW 不是实盘授权。") for i,t in enumerate(mat,1)],
            [HumanRecheckItem(f"human-{i}",r,statement=f"{r}：确认本项仅用于 Stage49 人工复查，不代表实盘授权；未来真实执行仍需单独审批。") for i,r in enumerate(roles,1)],
            [NextGrayCheckItem(f"gray-{i}",t,summary=f"下一轮灰度前检查“{t}”；仍不接实盘、不自动 approve、不调用 xttrader。") for i,t in enumerate(plan,1)])
def _decide(evidence):
    critical=[e for e in evidence if enum_value(e.severity)=='CRITICAL' or enum_value(e.status)=='FAIL']
    if critical: return LiveConsistencyDecision.NO_GO,[e.summary for e in critical]
    warn=[e for e in evidence if enum_value(e.severity)=='WARN' or enum_value(e.status) in {'WARN','SKIPPED'}]
    if warn: return LiveConsistencyDecision.NEED_MORE_EVIDENCE,[]
    return LiveConsistencyDecision.READY_FOR_CONSISTENCY_REVIEW,[]
def run_live_consistency(config:LiveConsistencyConfig|None=None, **kwargs:Any)->LiveConsistencyReport:
    cfg=config or build_default_live_consistency_config(**kwargs); assert_stage49_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization,cfg.live_trading_enabled,cfg.no_task_registered)
    ev=collect_live_consistency_evidence(cfg); decision,blocking=_decide(ev); warnings=[e.summary for e in ev if enum_value(e.severity)=='WARN' or enum_value(e.status) in {'WARN','SKIPPED'}]
    rem,mat,human,plan=_items(); summary={'total_evidence':len(ev),'critical':len(blocking),'warnings':len(warnings),'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'ready_for_consistency_review_not_trade_authorization':True}
    return LiveConsistencyReport(decision=decision,config=cfg,evidence=ev,remediation_review=rem,material_consistency=mat,human_recheck=human,next_gray_check_plan=plan,blocking_reasons=blocking,warnings=warnings,summary=summary)
def save_live_consistency_report(r, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_live_consistency_report_json(r) if p.suffix.lower()=='.json' else format_live_consistency_report_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_live_consistency_report_json(r),encoding='utf-8')
    return p
def load_live_consistency_report(path): return LiveConsistencyReport(**json.loads(Path(path).read_text(encoding='utf-8')))
def run_material_consistency(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveConsistencyReport) else run_live_consistency(report_or_config or build_default_live_consistency_config(**kw)); return MaterialConsistencyReport(decision=r.decision,items=r.material_consistency,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_material_consistency_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_material_consistency_report_json(r) if p.suffix.lower()=='.json' else format_material_consistency_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_material_consistency_report_json(r),encoding='utf-8')
def run_human_recheck(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveConsistencyReport) else run_live_consistency(report_or_config or build_default_live_consistency_config(**kw)); return HumanRecheckReport(decision=r.decision,items=r.human_recheck,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_human_recheck_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_human_recheck_report_json(r) if p.suffix.lower()=='.json' else format_human_recheck_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_human_recheck_report_json(r),encoding='utf-8')
def run_next_gray_check(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveConsistencyReport) else run_live_consistency(report_or_config or build_default_live_consistency_config(**kw)); return NextGrayCheckReport(decision=r.decision,items=r.next_gray_check_plan,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_next_gray_check_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_next_gray_check_report_json(r) if p.suffix.lower()=='.json' else format_next_gray_check_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_next_gray_check_report_json(r),encoding='utf-8')
