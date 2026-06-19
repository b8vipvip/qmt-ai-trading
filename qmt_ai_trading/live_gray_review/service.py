from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_gray_review_evidence
from .formatters import format_live_gray_review_report_json, format_live_gray_review_report_markdown, format_readonly_rehearsal_report_json, format_readonly_rehearsal_report_markdown
from .models import LiveGrayReviewConfig, LiveGrayReviewDecision as D, LiveGrayReviewReport, LiveGrayReviewSeverity as Sev, LiveGrayReviewStatus as S, ReadOnlyRehearsalReport, ReadOnlyRehearsalStep

def build_default_live_gray_review_config(repo_root: str|Path='.', **kwargs: Any) -> LiveGrayReviewConfig:
    cfg=LiveGrayReviewConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg

def _decide(evidence, items):
    critical=[x for x in [*evidence,*items] if getattr(x,'severity',None)==Sev.CRITICAL or getattr(x,'status',None)==S.FAIL]
    if critical: return D.NO_GO,[f"{getattr(x,'path','')}: {getattr(x,'summary',getattr(x,'message',''))}" for x in critical]
    missing=[x for x in evidence if getattr(x,'severity',None)==Sev.WARN or getattr(x,'status',None) in {S.WARN,S.SKIPPED}]
    if missing: return D.NEED_MORE_EVIDENCE,[]
    return D.READY_FOR_HUMAN_REVIEW,[]

def run_readonly_rehearsal(config: LiveGrayReviewConfig|None=None, decision: D|str=D.NEED_MORE_EVIDENCE) -> ReadOnlyRehearsalReport:
    steps=[ReadOnlyRehearsalStep('stage42-step-01','读取 Stage41 只读台账输出', evidence_path='live_gray_ledger_stage41/live_gray_ledger.json'),ReadOnlyRehearsalStep('stage42-step-02','汇总 Stage39/40/41 证据状态'),ReadOnlyRehearsalStep('stage42-step-03','生成只读人工复核包 Markdown/JSON'),ReadOnlyRehearsalStep('stage42-step-04','确认不产生交易授权、不触达真实账户')]
    return ReadOnlyRehearsalReport(decision=decision, steps=steps, summary={'read_only':True,'dry_run_only':True,'no_trade_authorization':True})

def run_live_gray_review(config: LiveGrayReviewConfig|None=None, **kwargs: Any) -> LiveGrayReviewReport:
    cfg=config or build_default_live_gray_review_config(**kwargs)
    evidence,items=collect_live_gray_review_evidence(cfg)
    decision,blocked=_decide(evidence,items)
    warnings=[f"{getattr(x,'path','')}: {getattr(x,'summary',getattr(x,'message',''))}" for x in [*evidence,*items] if getattr(x,'severity',None)==Sev.WARN or getattr(x,'status',None) in {S.WARN,S.SKIPPED}]
    rehearsal=run_readonly_rehearsal(cfg, decision)
    summary={'total_evidence':len(evidence),'total_checklist_items':len(items),'critical':len(blocked),'warnings':len(warnings),'ready_for_human_review_not_trade_authorization':True,'stage42_read_only':True}
    return LiveGrayReviewReport(decision=decision, config=cfg, evidence=evidence, checklist=items, rehearsal=rehearsal, blocking_reasons=blocked, warnings=warnings, summary=summary)

def save_live_gray_review_report(report: LiveGrayReviewReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(format_live_gray_review_report_json(report) if p.suffix.lower()=='.json' else format_live_gray_review_report_markdown(report), encoding='utf-8')
    if json_output:
        jp=Path(json_output); jp.parent.mkdir(parents=True, exist_ok=True); jp.write_text(format_live_gray_review_report_json(report), encoding='utf-8')
    return p

def save_readonly_rehearsal_report(report: ReadOnlyRehearsalReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(format_readonly_rehearsal_report_json(report) if p.suffix.lower()=='.json' else format_readonly_rehearsal_report_markdown(report), encoding='utf-8')
    if json_output:
        jp=Path(json_output); jp.parent.mkdir(parents=True, exist_ok=True); jp.write_text(format_readonly_rehearsal_report_json(report), encoding='utf-8')
    return p

def load_live_gray_review_report(path: str|Path) -> LiveGrayReviewReport:
    return LiveGrayReviewReport(**json.loads(Path(path).read_text(encoding='utf-8')))
