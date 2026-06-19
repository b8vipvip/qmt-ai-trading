from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_archive_evidence
from .formatters import *
from .models import *
from .safety import assert_stage48_read_only

def build_default_live_archive_config(repo_root: str|Path='.', **kwargs: Any) -> LiveArchiveConfig:
    cfg=LiveArchiveConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg
def _decide(evidence):
    critical=[x for x in evidence if x.severity==LiveArchiveSeverity.CRITICAL or x.status==LiveArchiveStatus.FAIL]
    if critical: return LiveArchiveDecision.NO_GO,[x.summary for x in critical]
    warn=[x for x in evidence if x.severity==LiveArchiveSeverity.WARN or x.status in {LiveArchiveStatus.WARN,LiveArchiveStatus.SKIPPED}]
    if warn: return LiveArchiveDecision.NEED_MORE_EVIDENCE,[]
    return LiveArchiveDecision.READY_FOR_ARCHIVE_REVIEW,[]
def _archive_index(evidence):
    titles=['Stage47 final review 文件索引','Stage47 signature verification 文件索引','Stage47 evidence gap report 文件索引','Stage47 next readonly plan 文件索引','Stage46 signoff 文件索引','Stage45 runbook 文件索引','Stage44 environment snapshot 文件索引','validation_logs 本地运行产物提示','.gitignore 忽略规则确认','归档材料不代表实盘授权声明']
    return [ArchiveIndexItem(item_id=f'archive-{i}',title=t,status=LiveArchiveStatus.PASS,summary=f'{t} 已纳入 Stage48 最终只读归档索引；不代表实盘授权。',confirmations=['只读材料状态','不调用 xttrader','不查询真实账户','不下单','不真实发送通知']) for i,t in enumerate(titles,1)]
def _remediation(evidence):
    titles=['Stage40 redline review 缺失补证计划','Stage43 NEED_MORE_EVIDENCE 补证计划','Stage44 NEED_MORE_EVIDENCE 补证计划','Stage45 NEED_MORE_EVIDENCE 补证计划','Stage46 NEED_MORE_EVIDENCE 补证计划','Stage47 NEED_MORE_EVIDENCE 补证计划','validation_logs 本地运行产物不提交说明','market_data / reports / logs 忽略规则说明','补证完成后重新执行只读验收说明']
    items=[EvidenceRemediationItem(item_id=f'remediation-{i}',title=t,summary=f'{t}：仅补齐本地只读证据，不产生实盘授权。') for i,t in enumerate(titles,1)]
    for e in evidence:
        if e.severity==LiveArchiveSeverity.WARN or e.status in {LiveArchiveStatus.WARN,LiveArchiveStatus.SKIPPED}:
            items.append(EvidenceRemediationItem(item_id=f'gap-{len(items)+1}',title=e.title or e.path,severity=LiveArchiveSeverity.WARN,summary=e.summary))
    return items
def _human():
    roles=['演练主持人核验状态','风险负责人核验状态','运行负责人核验状态','配置冻结复核人核验状态','最终授权人核验状态']
    return [HumanVerificationSummaryItem(item_id=f'human-{i}',role=r,statement=f'{r}：确认材料仅用于 Stage48 最终只读归档人工复核；不代表实盘授权；未来真实执行仍需单独审批。') for i,r in enumerate(roles,1)]
def _next():
    titles=['继续只读复核','缺口补证后复核','人工签字核验复核','配置冻结复查','运行产物忽略规则复查','不接实盘','不调用 xttrader','不真实下单','不查询真实账户','不真实通知','不注册真实任务']
    return [NextReadonlyCheckItem(item_id=f'check-{i}',title=t,summary=f'下一轮灰度前执行“{t}”检查；仍为只读材料，不产生任何实盘授权。') for i,t in enumerate(titles,1)]
def run_live_archive(config: LiveArchiveConfig|None=None, **kwargs: Any) -> LiveArchiveReport:
    cfg=config or build_default_live_archive_config(**kwargs); assert_stage48_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization,cfg.live_trading_enabled)
    evidence=collect_live_archive_evidence(cfg); decision,blocking=_decide(evidence); warnings=[x.summary for x in evidence if x.severity==LiveArchiveSeverity.WARN or x.status in {LiveArchiveStatus.WARN,LiveArchiveStatus.SKIPPED}]
    summary={'total_evidence':len(evidence),'critical':len(blocking),'warnings':len(warnings),'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'ready_for_archive_review_not_trade_authorization':True}
    return LiveArchiveReport(decision=decision,config=cfg,evidence=evidence,archive_index=_archive_index(evidence),evidence_remediation_plan=_remediation(evidence),human_verification_summary=_human(),next_readonly_check_plan=_next(),blocking_reasons=blocking,warnings=warnings,summary=summary)
def save_live_archive_report(report, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_live_archive_report_json(report) if p.suffix.lower()=='.json' else format_live_archive_report_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_live_archive_report_json(report),encoding='utf-8')
    return p
def load_live_archive_report(path): return LiveArchiveReport(**json.loads(Path(path).read_text(encoding='utf-8')))
def run_evidence_remediation(report_or_config=None, **kwargs):
    report=report_or_config if isinstance(report_or_config,LiveArchiveReport) else run_live_archive(report_or_config or build_default_live_archive_config(**kwargs))
    return EvidenceRemediationReport(decision=report.decision,items=report.evidence_remediation_plan,warnings=report.warnings,blocking_reasons=report.blocking_reasons,summary=report.summary)
def save_evidence_remediation_report(report, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_evidence_remediation_report_json(report) if p.suffix.lower()=='.json' else format_evidence_remediation_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_evidence_remediation_report_json(report),encoding='utf-8')
    return p
def run_human_verification_summary(report_or_config=None, **kwargs):
    report=report_or_config if isinstance(report_or_config,LiveArchiveReport) else run_live_archive(report_or_config or build_default_live_archive_config(**kwargs))
    return HumanVerificationSummaryReport(decision=report.decision,items=report.human_verification_summary,warnings=report.warnings,blocking_reasons=report.blocking_reasons,summary=report.summary)
def save_human_verification_summary_report(report, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_human_verification_summary_report_json(report) if p.suffix.lower()=='.json' else format_human_verification_summary_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_human_verification_summary_report_json(report),encoding='utf-8')
    return p
def run_next_readonly_check(report_or_config=None, **kwargs):
    report=report_or_config if isinstance(report_or_config,LiveArchiveReport) else run_live_archive(report_or_config or build_default_live_archive_config(**kwargs))
    return NextReadonlyCheckReport(decision=report.decision,items=report.next_readonly_check_plan,warnings=report.warnings,blocking_reasons=report.blocking_reasons,summary=report.summary)
def save_next_readonly_check_report(report, output_path, json_output=None):
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(format_next_readonly_check_report_json(report) if p.suffix.lower()=='.json' else format_next_readonly_check_markdown(report),encoding='utf-8')
    if json_output: Path(json_output).parent.mkdir(parents=True,exist_ok=True); Path(json_output).write_text(format_next_readonly_check_report_json(report),encoding='utf-8')
    return p
