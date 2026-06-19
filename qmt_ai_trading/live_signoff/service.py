from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_signoff_evidence
from .formatters import *
from .models import IncidentRehearsalReport, IncidentRehearsalResult, LiveSignoffConfig, LiveSignoffDecision as D, LiveSignoffReport, LiveSignoffSeverity as Sev, LiveSignoffStatus as S, ManualSignoffItem, ManualSignoffReport, RunbookReviewItem
from .safety import assert_stage46_read_only

def build_default_live_signoff_config(repo_root: str|Path='.', **kwargs: Any) -> LiveSignoffConfig:
    cfg=LiveSignoffConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg
def _review():
    titles=['Stage45 运行手册读取状态','Stage45 人工流程演练读取状态','Stage45 异常处理清单读取状态','安全声明复核','只读运行步骤复核','禁止动作复核','Risk Gate / Human Approval 边界复核','调度 preview 复核','运行产物忽略规则复核','go/no-go 材料状态']
    return [RunbookReviewItem(item_id=f'review-{i}',title=t,summary='仅复核只读材料状态，不产生实盘授权。',confirmations=['不调用 xttrader','不查询真实账户','不下单','不真实发送通知']) for i,t in enumerate(titles,1)]
def _manual():
    roles=['演练主持人签字项','风险负责人签字项','运行负责人签字项','配置冻结复核人签字项','最终授权人签字项']
    return [ManualSignoffItem(item_id=f'signoff-{i}',role=r,statement=f'{r}确认本材料只用于人工复核签字封版；不代表实盘授权；未来真实执行仍需单独审批。') for i,r in enumerate(roles,1)]
def _incidents():
    names=['数据缓存不足','Risk Gate 拒绝','Human Approval 缺失','Scheduler preview 异常','报告生成失败','发现真实交易 marker','发现敏感文件或运行产物误提交','发现 scripts/sync_all.ps1 被修改']
    return [IncidentRehearsalResult(item_id=f'incident-{i}',scenario=n,severity=Sev.CRITICAL if i>=6 else Sev.WARN,result='只读异常演练结果摘要已生成，待人工会议复核。',required_action='停止推进材料状态，记录证据路径，人工修复后重新验收。') for i,n in enumerate(names,1)]
def _decide(evidence):
    critical=[x for x in evidence if x.severity==Sev.CRITICAL or x.status==S.FAIL]
    if critical: return D.NO_GO,[x.summary for x in critical]
    warn=[x for x in evidence if x.severity==Sev.WARN or x.status in {S.WARN,S.SKIPPED}]
    if warn: return D.NEED_MORE_EVIDENCE,[]
    return D.READY_FOR_SIGNOFF_REVIEW,[]
def run_live_signoff(config: LiveSignoffConfig|None=None, **kwargs: Any) -> LiveSignoffReport:
    cfg=config or build_default_live_signoff_config(**kwargs); assert_stage46_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization,cfg.live_trading_enabled)
    evidence=collect_live_signoff_evidence(cfg); decision,blocking=_decide(evidence); warnings=[x.summary for x in evidence if x.severity==Sev.WARN or x.status in {S.WARN,S.SKIPPED}]
    summary={'total_evidence':len(evidence),'critical':len(blocking),'warnings':len(warnings),'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'ready_for_signoff_review_not_trade_authorization':True}
    return LiveSignoffReport(decision=decision,config=cfg,evidence=evidence,runbook_review=_review(),manual_signoff_items=_manual(),incident_results=_incidents(),blocking_reasons=blocking,warnings=warnings,summary=summary)
def save_live_signoff_report(report: LiveSignoffReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_live_signoff_report_json(report) if p.suffix.lower()=='.json' else format_live_signoff_report_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_live_signoff_report_json(report),encoding='utf-8')
    return p
def load_live_signoff_report(path: str|Path) -> LiveSignoffReport: return LiveSignoffReport(**json.loads(Path(path).read_text(encoding='utf-8')))
def run_manual_signoff(report_or_config: LiveSignoffReport|LiveSignoffConfig|None=None, **kwargs):
    report=report_or_config if isinstance(report_or_config,LiveSignoffReport) else run_live_signoff(report_or_config or build_default_live_signoff_config(**kwargs))
    return ManualSignoffReport(decision=report.decision,items=report.manual_signoff_items,warnings=report.warnings,blocking_reasons=report.blocking_reasons,summary=report.summary)
def save_manual_signoff_report(report: ManualSignoffReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_manual_signoff_report_json(report) if p.suffix.lower()=='.json' else format_manual_signoff_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_manual_signoff_report_json(report),encoding='utf-8')
    return p
def run_incident_rehearsal(report_or_config: LiveSignoffReport|LiveSignoffConfig|None=None, **kwargs):
    report=report_or_config if isinstance(report_or_config,LiveSignoffReport) else run_live_signoff(report_or_config or build_default_live_signoff_config(**kwargs))
    return IncidentRehearsalReport(decision=report.decision,items=report.incident_results,warnings=report.warnings,blocking_reasons=report.blocking_reasons,summary=report.summary)
def save_incident_rehearsal_report(report: IncidentRehearsalReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_incident_rehearsal_report_json(report) if p.suffix.lower()=='.json' else format_incident_rehearsal_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_incident_rehearsal_report_json(report),encoding='utf-8')
    return p
