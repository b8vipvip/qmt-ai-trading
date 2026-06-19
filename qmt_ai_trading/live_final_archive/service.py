from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_final_archive_evidence
from .formatters import *
from .models import *
from .safety import assert_stage50_read_only

def build_default_live_final_archive_config(repo_root: str|Path='.', **kwargs: Any) -> LiveFinalArchiveConfig:
    cfg=LiveFinalArchiveConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg
def _items():
    rem=["Stage49 consistency 读取状态","Stage48 archive 读取状态","Stage47 final review 读取状态","Stage46 signoff 读取状态","最终归档材料索引","本地只读证据路径复核","运行产物忽略规则复核","当前材料状态","下一步人工复核要求","不代表实盘授权声明"]
    mat=["Stage46 / Stage47 / Stage48 / Stage49 决策一致性","read_only 一致性","dry_run_only 一致性","no_trade_authorization 一致性","live_trading_enabled=false 或 live disabled 说明一致性","no_task_registered 一致性","Risk Gate / Human Approval 边界声明一致性","不调用 xttrader 声明一致性","不真实下单声明一致性","不真实通知声明一致性"]
    roles=["演练主持人复查","风险负责人复查","运行负责人复查","配置冻结复核人复查","最终授权人复查"]
    plan=["最终归档复核","材料一致性封版","人工核验复查","配置冻结复查","Risk Gate / Human Approval 边界复查","不接实盘","不调用 xttrader","不真实下单","不查询真实账户","不真实通知","不注册真实任务"]
    return ([FinalArchiveReviewItem(f"remediation-{i}",t,summary=f"{t}：只读复核材料状态，不代表实盘授权。") for i,t in enumerate(rem,1)],
            [MaterialSealItem(f"material-{i}",t,summary=f"{t}：保持 Stage46-49 材料边界一致；READY_FOR_FINAL_ARCHIVE_REVIEW 不是实盘授权。") for i,t in enumerate(mat,1)],
            [HumanClosureItem(f"human-{i}",r,statement=f"{r}：确认本项仅用于 Stage50 人工复查，不代表实盘授权；未来真实执行仍需单独审批。") for i,r in enumerate(roles,1)],
            [NextReadonlyCheckItem(f"gray-{i}",t,summary=f"下一轮灰度前检查“{t}”；仍不接实盘、不自动 approve、不调用 xttrader。") for i,t in enumerate(plan,1)])
def _decide(evidence):
    critical=[e for e in evidence if enum_value(e.severity)=='CRITICAL' or enum_value(e.status)=='FAIL']
    if critical: return LiveFinalArchiveDecision.NO_GO,[e.summary for e in critical]
    stage49=[e for e in evidence if enum_value(e.category)=='STAGE49_CONSISTENCY' and e.decision]
    if any(e.decision=='NEED_MORE_EVIDENCE' for e in stage49):
        return LiveFinalArchiveDecision.NEED_MORE_EVIDENCE,[]
    warn=[e for e in evidence if enum_value(e.severity)=='WARN' or enum_value(e.status) in {'WARN','SKIPPED'}]
    if warn: return LiveFinalArchiveDecision.NEED_MORE_EVIDENCE,[]
    return LiveFinalArchiveDecision.READY_FOR_FINAL_ARCHIVE_REVIEW,[]
def run_live_final_archive(config:LiveFinalArchiveConfig|None=None, **kwargs:Any)->LiveFinalArchiveReport:
    cfg=config or build_default_live_final_archive_config(**kwargs); assert_stage50_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization,cfg.live_trading_enabled,cfg.no_task_registered)
    ev=collect_live_final_archive_evidence(cfg); decision,blocking=_decide(ev); warnings=[e.summary for e in ev if enum_value(e.severity)=='WARN' or enum_value(e.status) in {'WARN','SKIPPED'}]
    rem,mat,human,plan=_items(); summary={'total_evidence':len(ev),'critical':len(blocking),'warnings':len(warnings),'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'ready_for_final_archive_review_not_trade_authorization':True}
    return LiveFinalArchiveReport(decision=decision,config=cfg,evidence=ev,final_archive_review=rem,material_seal=mat,human_closure=human,next_readonly_check_plan=plan,blocking_reasons=blocking,warnings=warnings,summary=summary)
def save_live_final_archive_report(r, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_live_final_archive_report_json(r) if p.suffix.lower()=='.json' else format_live_final_archive_report_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_live_final_archive_report_json(r),encoding='utf-8')
    return p
def load_live_final_archive_report(path): return LiveFinalArchiveReport(**json.loads(Path(path).read_text(encoding='utf-8')))
def run_material_seal(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveFinalArchiveReport) else run_live_final_archive(report_or_config or build_default_live_final_archive_config(**kw)); return MaterialSealReport(decision=r.decision,items=r.material_seal,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_material_seal_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_material_seal_report_json(r) if p.suffix.lower()=='.json' else format_material_seal_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_material_seal_report_json(r),encoding='utf-8')
def run_human_closure(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveFinalArchiveReport) else run_live_final_archive(report_or_config or build_default_live_final_archive_config(**kw)); return HumanClosureReport(decision=r.decision,items=r.human_closure,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_human_closure_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_human_closure_report_json(r) if p.suffix.lower()=='.json' else format_human_closure_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_human_closure_report_json(r),encoding='utf-8')
def run_next_readonly_check(report_or_config=None, **kw):
    r=report_or_config if isinstance(report_or_config,LiveFinalArchiveReport) else run_live_final_archive(report_or_config or build_default_live_final_archive_config(**kw)); return NextReadonlyCheckReport(decision=r.decision,items=r.next_readonly_check_plan,warnings=r.warnings,blocking_reasons=r.blocking_reasons,summary=r.summary)
def save_next_readonly_check_report(r,out,json_output=None):
    p=Path(out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_next_readonly_check_report_json(r) if p.suffix.lower()=='.json' else format_next_readonly_check_markdown(r),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_next_readonly_check_report_json(r),encoding='utf-8')
