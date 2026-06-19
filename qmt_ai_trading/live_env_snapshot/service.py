from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_env_snapshot_evidence
from .formatters import format_live_env_snapshot_report_json, format_live_env_snapshot_report_markdown, format_readonly_environment_snapshot_markdown, format_readonly_environment_snapshot_report_json
from .models import LiveEnvSnapshotConfig, LiveEnvSnapshotDecision as D, LiveEnvSnapshotReport, LiveEnvSnapshotSeverity as Sev, LiveEnvSnapshotStatus as S, ReadonlyEnvironmentSnapshotReport
from .safety import assert_stage44_read_only

def build_default_live_env_snapshot_config(repo_root: str|Path='.', **kwargs: Any) -> LiveEnvSnapshotConfig:
    cfg=LiveEnvSnapshotConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v,Path) else v)
    return cfg

def _decide(evidence, freeze, snapshots):
    all_items=[*evidence,*freeze,*snapshots]
    critical=[x for x in all_items if getattr(x,'severity',None)==Sev.CRITICAL or getattr(x,'status',None)==S.FAIL]
    if critical: return D.NO_GO,[f"{getattr(x,'path',getattr(x,'name',''))}: {getattr(x,'summary','')}" for x in critical if getattr(x,'summary','')]
    missing=[x for x in all_items if getattr(x,'severity',None)==Sev.WARN or getattr(x,'status',None) in {S.WARN,S.SKIPPED}]
    if missing: return D.NEED_MORE_EVIDENCE,[]
    return D.READY_FOR_ENV_SNAPSHOT,[]

def _warnings(items): return [f"{getattr(x,'path',getattr(x,'name',''))}: {getattr(x,'summary','No details provided.')}" for x in items if (getattr(x,'severity',None)==Sev.WARN or getattr(x,'status',None) in {S.WARN,S.SKIPPED}) and getattr(x,'summary','')]

def run_live_env_snapshot(config: LiveEnvSnapshotConfig|None=None, **kwargs: Any) -> LiveEnvSnapshotReport:
    cfg=config or build_default_live_env_snapshot_config(**kwargs); assert_stage44_read_only(cfg.read_only,cfg.dry_run_only,cfg.no_trade_authorization,cfg.live_trading_enabled)
    evidence,freeze,snapshots=collect_live_env_snapshot_evidence(cfg); decision,blocked=_decide(evidence,freeze,snapshots); warnings=_warnings([*evidence,*freeze,*snapshots])
    summary={'total_evidence':len(evidence),'config_freeze_review_items':len(freeze),'environment_snapshot_items':len(snapshots),'critical':len(blocked),'warnings':len(warnings),'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'live_trading_enabled':False,'ready_for_env_snapshot_not_trade_authorization':True}
    return LiveEnvSnapshotReport(decision=decision, config=cfg, evidence=evidence, config_freeze_review=freeze, environment_snapshot=snapshots, blocking_reasons=blocked, warnings=warnings, summary=summary)

def save_live_env_snapshot_report(report: LiveEnvSnapshotReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(format_live_env_snapshot_report_json(report) if p.suffix.lower()=='.json' else format_live_env_snapshot_report_markdown(report), encoding='utf-8')
    if json_output:
        jp=Path(json_output); jp.parent.mkdir(parents=True, exist_ok=True); jp.write_text(format_live_env_snapshot_report_json(report), encoding='utf-8')
    return p

def load_live_env_snapshot_report(path: str|Path) -> LiveEnvSnapshotReport:
    return LiveEnvSnapshotReport(**json.loads(Path(path).read_text(encoding='utf-8')))

def run_readonly_environment_snapshot(report_or_config: LiveEnvSnapshotReport|LiveEnvSnapshotConfig|None=None, **kwargs: Any) -> ReadonlyEnvironmentSnapshotReport:
    report = report_or_config if isinstance(report_or_config, LiveEnvSnapshotReport) else run_live_env_snapshot(report_or_config or build_default_live_env_snapshot_config(**kwargs))
    return ReadonlyEnvironmentSnapshotReport(decision=report.decision, config=report.config, items=report.environment_snapshot, warnings=report.warnings, blocking_reasons=report.blocking_reasons, summary={'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'live_trading_enabled':False})

def save_readonly_environment_snapshot_report(report: ReadonlyEnvironmentSnapshotReport, output_path: str|Path, json_output: str|Path|None=None):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(format_readonly_environment_snapshot_report_json(report) if p.suffix.lower()=='.json' else format_readonly_environment_snapshot_markdown(report), encoding='utf-8')
    if json_output:
        jp=Path(json_output); jp.parent.mkdir(parents=True, exist_ok=True); jp.write_text(format_readonly_environment_snapshot_report_json(report), encoding='utf-8')
    return p
