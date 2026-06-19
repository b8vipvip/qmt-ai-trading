from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .collector import collect_live_gray_ledger_evidence
from .formatters import format_live_gray_ledger_report_json, format_live_gray_ledger_report_markdown
from .models import LiveGrayLedgerConfig, LiveGrayLedgerDecision as D, LiveGrayLedgerReport, LiveGrayLedgerSeverity as Sev, LiveGrayLedgerStatus as S, to_plain

def build_default_live_gray_ledger_config(repo_root: str | Path='.', **kwargs: Any) -> LiveGrayLedgerConfig:
    cfg=LiveGrayLedgerConfig(repo_root=str(repo_root))
    for k,v in kwargs.items():
        if v is not None and hasattr(cfg,k): setattr(cfg,k,str(v) if isinstance(v, Path) else v)
    return cfg

def _decide(evidence, items):
    critical=[x for x in [*evidence,*items] if getattr(x,'severity',None)==Sev.CRITICAL or getattr(x,'status',None)==S.FAIL]
    if critical: return D.BLOCKED, [f"{getattr(x,'path','')}: {getattr(x,'summary', getattr(x,'message',''))}" for x in critical]
    missing=[x for x in evidence if x.status in {S.WARN,S.SKIPPED}]
    if missing: return D.NEED_MORE_EVIDENCE, []
    return D.READY_FOR_MANUAL_REVIEW, []

def run_live_gray_ledger(config: LiveGrayLedgerConfig | None=None, **kwargs: Any) -> LiveGrayLedgerReport:
    cfg=config or build_default_live_gray_ledger_config(**kwargs)
    evidence, items=collect_live_gray_ledger_evidence(cfg)
    decision, blocked=_decide(evidence, items)
    warnings=[f"{getattr(x,'path','')}: {getattr(x,'summary', getattr(x,'message',''))}" for x in [*evidence,*items] if getattr(x,'severity',None)==Sev.WARN or getattr(x,'status',None) in {S.WARN,S.SKIPPED}]
    summary={"total_evidence":len(evidence),"total_items":len(items),"critical":len(blocked),"warnings":len(warnings),"ready_for_manual_review_not_trade_authorization":True,"stage41_read_only":True}
    return LiveGrayLedgerReport(decision=decision, config=cfg, evidence=evidence, items=items, blocked_reasons=blocked, warnings=warnings, summary=summary)

def save_live_gray_ledger_report(report: LiveGrayLedgerReport, output_path: str | Path, json_output: str | Path | None=None):
    path=Path(output_path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_live_gray_ledger_report_json(report) if path.suffix.lower()=='.json' else format_live_gray_ledger_report_markdown(report), encoding='utf-8')
    if json_output:
        jp=Path(json_output); jp.parent.mkdir(parents=True, exist_ok=True); jp.write_text(format_live_gray_ledger_report_json(report), encoding='utf-8')
    return path

def load_live_gray_ledger_report(path: str | Path) -> LiveGrayLedgerReport:
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    return LiveGrayLedgerReport(**data)
