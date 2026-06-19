from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_runbook_evidence
from .formatters import format_incident_playbook_markdown, format_incident_playbook_report_json, format_live_runbook_report_json, format_live_runbook_report_markdown, format_manual_rehearsal_markdown, format_manual_rehearsal_report_json
from .models import IncidentPlaybookItem, IncidentPlaybookReport, LiveRunbookConfig, LiveRunbookDecision as D, LiveRunbookReport, LiveRunbookSeverity as Sev, LiveRunbookStatus as S, ManualRehearsalReport, ManualRehearsalStep, RunbookSection
from .safety import assert_stage45_read_only

def build_default_live_runbook_config(repo_root: str|Path='.', **kwargs: Any) -> LiveRunbookConfig:
    cfg=LiveRunbookConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg

def _sections():
    titles=['本阶段安全声明','系统当前状态摘要','可执行的只读检查步骤','禁止执行的真实交易动作','人工确认流程','Risk Gate 与 Human Approval 边界','调度任务 preview 流程','运行产物清理与忽略规则','异常处理与回滚流程','下一阶段 Stage46 预告']
    return [RunbookSection(section_id=f'section-{i}', title=t, content=[
        '仅读取本地 Markdown/JSON/.gitignore 与 Stage41-Stage44 证据。',
        '不得执行真实交易、账户查询、真实通知或自动审批。',
        '所有结论只用于人工会议复核。' if i<10 else 'Stage46 仍不得直接实盘，只能继续复核、演练签字和只读检查。'
    ]) for i,t in enumerate(titles,1)]
def _steps():
    titles=['演练前检查','只读运行手册复核','人工审批边界确认','风控边界确认','调度 preview 确认','异常场景演练','go/no-go 会议材料确认']
    return [ManualRehearsalStep(step_id=f'step-{i}', title=t, checklist=['确认 dry-run/shadow 默认开启','确认无真实账户查询、无真实委托、无真实通知','确认需要人工签字后才能进入后续材料阶段'], expected_result='仅形成会议复核记录，不产生实盘授权。') for i,t in enumerate(titles,1)]
def _incidents():
    names=['数据缓存不足','Risk Gate 拒绝','Human Approval 缺失','Scheduler preview 异常','报告生成失败','发现真实交易 marker','发现敏感文件或运行产物误提交','发现 scripts/sync_all.ps1 被修改']
    return [IncidentPlaybookItem(item_id=f'incident-{i}', scenario=n, severity=Sev.CRITICAL if i>=6 else Sev.WARN, detection='只读检查、人工复核或验证脚本发现异常。', response=['停止推进 go/no-go 材料状态','记录证据路径与复现命令','由人工确认修复后重新运行 Stage45 验证'], rollback='回退相关材料变更；若涉及 sync_all.ps1，立即恢复该文件且不得提交。') for i,n in enumerate(names,1)]
def _decide(evidence):
    critical=[x for x in evidence if x.severity==Sev.CRITICAL or x.status==S.FAIL]
    if critical: return D.NO_GO,[x.summary for x in critical]
    warn=[x for x in evidence if x.severity==Sev.WARN or x.status in {S.WARN,S.SKIPPED}]
    if warn: return D.NEED_MORE_EVIDENCE,[]
    return D.READY_FOR_RUNBOOK_REVIEW,[]
def run_live_runbook(config: LiveRunbookConfig|None=None, **kwargs: Any) -> LiveRunbookReport:
    cfg=config or build_default_live_runbook_config(**kwargs); assert_stage45_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization,cfg.live_trading_enabled)
    evidence=collect_live_runbook_evidence(cfg); decision,blocking=_decide(evidence)
    warnings=[x.summary for x in evidence if x.severity==Sev.WARN or x.status in {S.WARN,S.SKIPPED}]
    summary={'total_evidence':len(evidence),'critical':len(blocking),'warnings':len(warnings),'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'live_trading_enabled':False,'ready_for_runbook_review_not_trade_authorization':True}
    return LiveRunbookReport(decision=decision, config=cfg, evidence=evidence, runbook_sections=_sections(), manual_steps=_steps(), incident_items=_incidents(), blocking_reasons=blocking, warnings=warnings, summary=summary)
def save_live_runbook_report(report: LiveRunbookReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_live_runbook_report_json(report) if p.suffix.lower()=='.json' else format_live_runbook_report_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_live_runbook_report_json(report),encoding='utf-8')
    return p
def load_live_runbook_report(path: str|Path) -> LiveRunbookReport: return LiveRunbookReport(**json.loads(Path(path).read_text(encoding='utf-8')))
def run_manual_rehearsal(report_or_config: LiveRunbookReport|LiveRunbookConfig|None=None, **kwargs):
    report=report_or_config if isinstance(report_or_config,LiveRunbookReport) else run_live_runbook(report_or_config or build_default_live_runbook_config(**kwargs))
    return ManualRehearsalReport(decision=report.decision, steps=report.manual_steps, warnings=report.warnings, blocking_reasons=report.blocking_reasons, summary=report.summary)
def save_manual_rehearsal_report(report: ManualRehearsalReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_manual_rehearsal_report_json(report) if p.suffix.lower()=='.json' else format_manual_rehearsal_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_manual_rehearsal_report_json(report),encoding='utf-8')
    return p
def run_incident_playbook(report_or_config: LiveRunbookReport|LiveRunbookConfig|None=None, **kwargs):
    report=report_or_config if isinstance(report_or_config,LiveRunbookReport) else run_live_runbook(report_or_config or build_default_live_runbook_config(**kwargs))
    return IncidentPlaybookReport(decision=report.decision, items=report.incident_items, warnings=report.warnings, blocking_reasons=report.blocking_reasons, summary=report.summary)
def save_incident_playbook_report(report: IncidentPlaybookReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_incident_playbook_report_json(report) if p.suffix.lower()=='.json' else format_incident_playbook_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_incident_playbook_report_json(report),encoding='utf-8')
    return p
