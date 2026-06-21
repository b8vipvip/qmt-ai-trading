"""Dry-run circuit-breaker decisions for monitoring reports."""

from __future__ import annotations

from collections.abc import Iterable

from .models import CircuitBreakerDecision, MonitoringEvent
from .rules import max_severity


def decide_circuit_breaker(events: Iterable[MonitoringEvent]) -> CircuitBreakerDecision:
    event_list = list(events)
    severity = max_severity(event_list)
    if severity == "CRITICAL":
        critical_names = ", ".join(event.name for event in event_list if event.severity == "CRITICAL")
        return CircuitBreakerDecision("OPEN", True, f"Critical monitoring event(s): {critical_names}", severity)
    if severity in {"WARNING", "ERROR"}:
        return CircuitBreakerDecision("HALF_OPEN", False, "Warnings require human review before live readiness.", severity)
    return CircuitBreakerDecision("CLOSED", False, "No blocking monitoring events detected.", severity)


STAGE83_CRITICAL_RULES = {'UNSAFE_AGENT_OUTPUT','FORBIDDEN_TERM_DETECTED','HIGH_DRAWDOWN','RISK_GATE_BYPASS_ATTEMPT','AUTO_APPROVE_DETECTED','LIVE_TRADE_TERM_DETECTED','QMT_TRADER_API_DETECTED','ORDER_SUBMIT_DETECTED'}

class CircuitBreakerSimulator:
    def evaluate(self, alerts, ctx):
        triggered=[a['rule_id'] for a in alerts if a['severity'] in {'HIGH','CRITICAL'} or a['rule_id'] in STAGE83_CRITICAL_RULES]
        status='NORMAL'
        if any(a['severity']=='CRITICAL' or a['rule_id'] in STAGE83_CRITICAL_RULES for a in alerts): status='DRY_RUN_BLOCKED'
        elif triggered: status='REQUIRES_HUMAN_REVIEW'
        elif alerts: status='WATCH'
        return {'status':status,'triggered':status!='NORMAL','triggered_rules':sorted(set(triggered)),'blocked_actions':['real_notification','order_submission','account_query','risk_gate_override','auto_approval'] if status!='NORMAL' else [],'requires_human_review':True,'dry_run':True,'not_live_trading':True,'no_order_submitted':True,'no_qmt_trader_api':True}
