from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_signature_freeze_evidence
from .formatters import format_config_freeze_report_json, format_config_freeze_report_markdown, format_live_signature_freeze_report_json, format_live_signature_freeze_report_markdown
from .models import ConfigFreezeItem, ConfigFreezeReport, LiveSignatureFreezeConfig, LiveSignatureFreezeDecision as D, LiveSignatureFreezeReport, LiveSignatureFreezeSeverity as Sev, LiveSignatureFreezeStatus as S

def build_default_live_signature_freeze_config(repo_root: str|Path='.', **kwargs: Any) -> LiveSignatureFreezeConfig:
    cfg=LiveSignatureFreezeConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg

def _config_items(cfg):
    return [
        ConfigFreezeItem('stage43-freeze-01', name='read_only', frozen_value='True', summary='Stage43 only reads local Markdown/JSON evidence.'),
        ConfigFreezeItem('stage43-freeze-02', name='dry_run_only', frozen_value='True', summary='No live authorization or real order path is enabled.'),
        ConfigFreezeItem('stage43-freeze-03', name='review_dir', frozen_value=cfg.review_dir, summary='Stage42 human review package input directory.'),
        ConfigFreezeItem('stage43-freeze-04', name='ledger_dir', frozen_value=cfg.ledger_dir, summary='Stage41 ledger input directory.'),
        ConfigFreezeItem('stage43-freeze-05', name='redline_review_dir', frozen_value=cfg.redline_review_dir, summary='Stage40 red-line review input directory.'),
    ]

def _decide(evidence, items):
    critical=[x for x in [*evidence,*items] if getattr(x,'severity',None)==Sev.CRITICAL or getattr(x,'status',None)==S.FAIL]
    if critical: return D.NO_GO,[f"{getattr(x,'path','')}: {getattr(x,'summary',getattr(x,'message',''))}" for x in critical]
    missing=[x for x in evidence if getattr(x,'severity',None)==Sev.WARN or getattr(x,'status',None) in {S.WARN,S.SKIPPED}]
    if missing: return D.NEED_MORE_EVIDENCE,[]
    return D.READY_FOR_SIGNATURE,[]

def run_live_signature_freeze(config: LiveSignatureFreezeConfig|None=None, **kwargs: Any) -> LiveSignatureFreezeReport:
    cfg=config or build_default_live_signature_freeze_config(**kwargs)
    evidence,items=collect_live_signature_freeze_evidence(cfg)
    decision,blocked=_decide(evidence,items)
    warnings=[f"{getattr(x,'path','')}: {(getattr(x,'summary','') or getattr(x,'message','') or 'Warning details unavailable; manual review required.')}" for x in [*evidence,*items] if (getattr(x,'severity',None)==Sev.WARN or getattr(x,'status',None) in {S.WARN,S.SKIPPED})]
    freeze_items=_config_items(cfg)
    summary={'total_evidence':len(evidence),'total_checklist_items':len(items),'critical':len(blocked),'warnings':len(warnings),'ready_for_signature_not_trade_authorization':True,'stage43_read_only':True}
    return LiveSignatureFreezeReport(decision=decision, config=cfg, evidence=evidence, checklist=items, config_freeze_items=freeze_items, blocking_reasons=blocked, warnings=warnings, summary=summary)

def save_live_signature_freeze_report(report: LiveSignatureFreezeReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(format_live_signature_freeze_report_json(report) if p.suffix.lower()=='.json' else format_live_signature_freeze_report_markdown(report), encoding='utf-8')
    if json_output:
        jp=Path(json_output); jp.parent.mkdir(parents=True, exist_ok=True); jp.write_text(format_live_signature_freeze_report_json(report), encoding='utf-8')
    return p

def load_live_signature_freeze_report(path: str|Path) -> LiveSignatureFreezeReport:
    return LiveSignatureFreezeReport(**json.loads(Path(path).read_text(encoding='utf-8')))

def run_config_freeze_summary(report_or_config: LiveSignatureFreezeReport|LiveSignatureFreezeConfig|None=None, **kwargs: Any) -> ConfigFreezeReport:
    if isinstance(report_or_config, LiveSignatureFreezeReport):
        report=report_or_config; cfg=report.config if isinstance(report.config, LiveSignatureFreezeConfig) else build_default_live_signature_freeze_config(**report.config)
        return ConfigFreezeReport(decision=report.decision, config=cfg, items=report.config_freeze_items or _config_items(cfg), warnings=report.warnings, blocking_reasons=report.blocking_reasons, summary={'read_only':True,'not_trade_authorization':True})
    cfg=report_or_config or build_default_live_signature_freeze_config(**kwargs)
    report=run_live_signature_freeze(cfg)
    return run_config_freeze_summary(report)

def save_config_freeze_report(report: ConfigFreezeReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(format_config_freeze_report_json(report) if p.suffix.lower()=='.json' else format_config_freeze_report_markdown(report), encoding='utf-8')
    if json_output:
        jp=Path(json_output); jp.parent.mkdir(parents=True, exist_ok=True); jp.write_text(format_config_freeze_report_json(report), encoding='utf-8')
    return p
