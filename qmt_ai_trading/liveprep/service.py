from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .models import LiveGrayConfig, LiveGrayReadinessReport, LiveGrayCheckStatus as S, LiveGraySeverity as V, SAFETY_NOTE
from .gates import *
from .safety import build_default_live_gray_config, validate_live_gray_config, validate_no_live_execution_intent, sanitize_live_gray_metadata
from .checklist import default_gray_checklist_items
from .formatters import format_live_gray_report_json, format_live_gray_report_markdown

def _load(path: str | Path | None):
    if not path: return None
    p=Path(path)
    if not p.exists(): return None
    txt=p.read_text(encoding="utf-8")
    try: return json.loads(txt)
    except Exception: return {"text":txt,"status":"PRESENT"}

def run_live_gray_readiness_check(*, config: LiveGrayConfig | None=None, trade_intents=None, risk_decisions=None, approval_status=None, paper_status=None, audit_report=None, monitoring_report=None, agent_memo=None, circuit_breaker_decision=None, cache_quality_decision=None, metadata=None) -> LiveGrayReadinessReport:
    cfg=config or build_default_live_gray_config()
    checks=[]; checks+=validate_live_gray_config(cfg); checks+=check_live_switches(cfg); checks+=check_capital_limits(cfg); checks+=check_symbol_whitelist(cfg, trade_intents)
    checks+=check_risk_gate_required(cfg,risk_decisions); checks+=check_human_approval_required(cfg,approval_status); checks+=check_paper_trading_required(cfg,paper_status); checks+=check_live_readiness_audit_required(cfg,audit_report); checks+=check_monitoring_required(cfg,monitoring_report); checks+=check_agent_research_required(cfg,agent_memo); checks+=check_circuit_breaker_required(cfg,circuit_breaker_decision); checks+=check_quality_required(cfg,cache_quality_decision)
    decision=aggregate_live_gray_checks(checks,cfg)
    blocked=[c.message for c in checks if getattr(c.status,'value',c.status)==S.FAIL.value or getattr(c.severity,'value',c.severity)==V.CRITICAL.value]
    report=LiveGrayReadinessReport(decision=decision, config=cfg, checks=checks, summary={"total_checks":len(checks),"failed_checks":len(blocked),"warn_checks":sum(1 for c in checks if getattr(c.status,'value',c.status)==S.WARN.value),"passed_checks":sum(1 for c in checks if getattr(c.status,'value',c.status)==S.PASS.value)}, blocked_reasons=blocked, manual_review_items=default_gray_checklist_items(), success=(str(getattr(decision,'value',decision))=="READY_FOR_MANUAL_REVIEW"), message=f"Decision={getattr(decision,'value',decision)}; preparation report only.", safety_note=SAFETY_NOTE, metadata=sanitize_live_gray_metadata(metadata))
    report.checks.append(validate_no_live_execution_intent(report))
    return report

def run_live_gray_readiness_from_files(*, config: LiveGrayConfig | None=None, pipeline_report=None, approval_file=None, paper_report=None, audit_report=None, monitoring_report=None, agent_memo=None, quality_report=None, **kwargs):
    pipe=_load(pipeline_report) or {}
    return run_live_gray_readiness_check(config=config, approval_status=_load(approval_file), paper_status=_load(paper_report), audit_report=_load(audit_report), monitoring_report=_load(monitoring_report), agent_memo=_load(agent_memo), cache_quality_decision=_load(quality_report), trade_intents=pipe.get("trade_intents") if isinstance(pipe,dict) else None, risk_decisions=pipe.get("risk_decisions") if isinstance(pipe,dict) else None, metadata={"input_files":{k:str(v) for k,v in {"pipeline_report":pipeline_report,"approval_file":approval_file,"paper_report":paper_report,"audit_report":audit_report,"monitoring_report":monitoring_report,"agent_memo":agent_memo,"quality_report":quality_report}.items() if v}, **kwargs})

def save_live_gray_readiness_report(report, output_path):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
    text=format_live_gray_report_json(report) if p.suffix.lower()==".json" else format_live_gray_report_markdown(report)
    p.write_text(text, encoding="utf-8"); return p

def load_live_gray_readiness_report(path):
    data=json.loads(Path(path).read_text(encoding="utf-8")); return data
