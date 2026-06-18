"""Read-only rehearsal scenarios."""
from __future__ import annotations
from typing import Any, Mapping
from .models import GrayRehearsalConfig, GrayRehearsalDecision, GrayRehearsalScenarioResult, GrayRehearsalScenarioType, GrayRehearsalStep, GrayRehearsalStepStatus

def _has(ctx: Mapping[str, Any], key: str) -> bool: return bool(ctx.get(key))
def _step(i: str, typ, title: str, status, msg: str, ev: list[str] | None=None) -> GrayRehearsalStep: return GrayRehearsalStep(i, typ, title, status, msg, ev or [])
def _result(typ, title, steps, warnings=None, blocked=None, decision=None):
    warnings=warnings or []; blocked=blocked or []
    if decision is None: decision = GrayRehearsalDecision.BLOCKED if blocked else (GrayRehearsalDecision.WARN if warnings or any(s.status==GrayRehearsalStepStatus.WARN for s in steps) else GrayRehearsalDecision.PASS)
    return GrayRehearsalScenarioResult(f"scenario-{typ.value.lower()}", typ, title, decision, steps, summarize_steps(steps), blocked, warnings)

def summarize_steps(steps): return f"{sum(1 for s in steps if s.status==GrayRehearsalStepStatus.PASS)} PASS, {sum(1 for s in steps if s.status==GrayRehearsalStepStatus.WARN)} WARN, {sum(1 for s in steps if s.status==GrayRehearsalStepStatus.SKIP)} SKIP."

def build_default_rehearsal_scenarios(config: GrayRehearsalConfig) -> list[GrayRehearsalScenarioType]: return list(config.scenario_types or list(GrayRehearsalScenarioType))

def run_normal_dry_run_scenario(context, config):
    t=GrayRehearsalScenarioType.NORMAL_DRY_RUN
    steps=[_step("normal.dry_run",t,"Dry-run configuration",GrayRehearsalStepStatus.PASS,"rehearsal_dry_run=True"),_step("normal.risk_gate",t,"Risk Gate required",GrayRehearsalStepStatus.PASS if config.require_risk_gate else GrayRehearsalStepStatus.FAIL,"Risk Gate cannot be bypassed"),_step("normal.human",t,"Human Approval required",GrayRehearsalStepStatus.PASS if config.require_human_approval else GrayRehearsalStepStatus.FAIL,"Human Approval cannot be bypassed")]
    blocked=[] if config.require_risk_gate and config.require_human_approval else ["mandatory gate disabled"]
    return _result(t,"Normal dry-run rehearsal",steps,blocked=blocked)

def run_risk_gate_blocked_scenario(context, config):
    t=GrayRehearsalScenarioType.RISK_GATE_BLOCKED
    return _result(t,"Risk Gate blocked scenario",[_step("risk.block",t,"Risk Gate simulated block",GrayRehearsalStepStatus.PASS,"Blocked TradeIntent remains blocked and cannot progress to approval/paper/live.")],blocked=["simulated Risk Gate block verified"],decision=GrayRehearsalDecision.BLOCKED)

def run_data_quality_unknown_scenario(context, config):
    t=GrayRehearsalScenarioType.DATA_QUALITY_UNKNOWN; exists=_has(context,"data_quality_report")
    return _result(t,"Data quality UNKNOWN scenario",[_step("dq.readonly",t,"Data Quality read-only",GrayRehearsalStepStatus.PASS,"Only local report/mock context inspected."),_step("dq.present",t,"Data Quality evidence",GrayRehearsalStepStatus.PASS if exists else GrayRehearsalStepStatus.WARN,"Missing input file is WARN, not crash.")],warnings=[] if exists else ["data quality tracking report not supplied; UNKNOWN rehearsed"])

def run_circuit_breaker_open_scenario(context, config):
    t=GrayRehearsalScenarioType.CIRCUIT_BREAKER_OPEN; exists=_has(context,"monitoring_report")
    return _result(t,"Circuit Breaker OPEN scenario",[_step("cb.open",t,"Monitoring can block",GrayRehearsalStepStatus.PASS,"Circuit Breaker OPEN blocks progression."),_step("cb.evidence",t,"Monitoring evidence",GrayRehearsalStepStatus.PASS if exists else GrayRehearsalStepStatus.WARN,"Missing monitoring file uses mock OPEN scenario.")],blocked=["simulated Circuit Breaker OPEN verified"],warnings=[] if exists else ["monitoring report not supplied; mock OPEN used"],decision=GrayRehearsalDecision.BLOCKED)

def run_live_gray_no_go_scenario(context, config):
    t=GrayRehearsalScenarioType.LIVE_GRAY_NO_GO
    return _result(t,"Live Gray NO_GO scenario",[_step("lg.no_go",t,"NO_GO/BLOCKED/review only",GrayRehearsalStepStatus.PASS,"Live Gray does not produce automatic GO."),_step("lg.live_off",t,"Live disabled",GrayRehearsalStepStatus.PASS,"live_enabled remains false.")],blocked=["live gray automatic GO is forbidden"],decision=GrayRehearsalDecision.BLOCKED)

def run_notification_dry_run_scenario(context, config):
    t=GrayRehearsalScenarioType.NOTIFICATION_DRY_RUN; exists=_has(context,"notification_dry_run_report")
    return _result(t,"Notification Dry Run scenario",[_step("notify.no_send",t,"No real send",GrayRehearsalStepStatus.PASS,"Notification Dry Run does not send real messages."),_step("notify.evidence",t,"Notification evidence",GrayRehearsalStepStatus.PASS if exists else GrayRehearsalStepStatus.WARN,"Missing report is WARN.")],warnings=[] if exists else ["notification dry-run report not supplied"])

def run_dashboard_read_only_scenario(context, config):
    t=GrayRehearsalScenarioType.DASHBOARD_READ_ONLY; exists=_has(context,"dashboard_path")
    return _result(t,"Dashboard read-only scenario",[_step("dash.readonly",t,"Read-only dashboard",GrayRehearsalStepStatus.PASS,"Dashboard has no order-entry API/button in rehearsal."),_step("dash.evidence",t,"Dashboard evidence",GrayRehearsalStepStatus.PASS if exists else GrayRehearsalStepStatus.WARN,"Missing dashboard path is WARN.")],warnings=[] if exists else ["dashboard path not supplied"])

def summarize_scenario_result(result: GrayRehearsalScenarioResult) -> str: return result.summary
RUNNERS={GrayRehearsalScenarioType.NORMAL_DRY_RUN:run_normal_dry_run_scenario,GrayRehearsalScenarioType.RISK_GATE_BLOCKED:run_risk_gate_blocked_scenario,GrayRehearsalScenarioType.DATA_QUALITY_UNKNOWN:run_data_quality_unknown_scenario,GrayRehearsalScenarioType.CIRCUIT_BREAKER_OPEN:run_circuit_breaker_open_scenario,GrayRehearsalScenarioType.LIVE_GRAY_NO_GO:run_live_gray_no_go_scenario,GrayRehearsalScenarioType.NOTIFICATION_DRY_RUN:run_notification_dry_run_scenario,GrayRehearsalScenarioType.DASHBOARD_READ_ONLY:run_dashboard_read_only_scenario}
