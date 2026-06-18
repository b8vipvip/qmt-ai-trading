from __future__ import annotations
from typing import Any, Iterable, Mapping
from .models import LiveGrayCheck, LiveGrayCheckStatus as S, LiveGraySeverity as V, LiveGrayScope as C, LiveGrayConfig, LiveGrayDecision

def _c(i,scope,status,sev,title,msg,e=None,rem=""): return LiveGrayCheck(i,scope,status,sev,title,msg,dict(e or {}),rem)
def _get(obj: Any, key: str, default=None):
    if obj is None: return default
    if isinstance(obj, Mapping): return obj.get(key, default)
    return getattr(obj, key, default)
def _status_text(obj: Any) -> str: return str(_get(obj,"status",_get(obj,"decision",_get(obj,"state",_get(obj,"quality_level",obj))))).upper()

def check_live_switches(config: LiveGrayConfig):
    checks=[]
    checks.append(_c("live_switch",C.CONFIG,S.SKIP if not config.live_enabled else S.FAIL,V.INFO if not config.live_enabled else V.CRITICAL,"Live switch","live_enabled=False: NO_GO by design." if not config.live_enabled else "live_enabled=True is blocked in Stage 30.",{"live_enabled":config.live_enabled}))
    checks.append(_c("gray_switch",C.CONFIG,S.SKIP if not config.gray_enabled else S.PASS,V.INFO,"Gray switch","gray_enabled=False: NO_GO by design." if not config.gray_enabled else "gray_enabled=True: manual review candidate only.",{"gray_enabled":config.gray_enabled}))
    return checks

def check_capital_limits(config: LiveGrayConfig):
    checks=[]
    limits=[("max_total_capital",config.max_total_capital,5000), ("max_single_order_value",config.max_single_order_value,1000), ("max_symbol_weight",config.max_symbol_weight,0.1), ("max_portfolio_weight",config.max_portfolio_weight,0.2)]
    for name,val,limit in limits:
        ok=0 < float(val) <= limit
        checks.append(_c(name,C.CAPITAL,S.PASS if ok else S.FAIL,V.INFO if ok else V.ERROR,name,f"{name}={val} within small gray cap {limit}." if ok else f"{name}={val} exceeds allowed gray cap {limit}.",{name:val,"limit":limit},"Lower the gray readiness limit."))
    return checks

def check_symbol_whitelist(config: LiveGrayConfig, trade_intents: Iterable[Any] | None=None):
    allowed={str(s).strip().upper() for s in config.allowed_symbols if str(s).strip()}
    checks=[_c("symbol_whitelist_non_empty",C.WHITELIST,S.PASS if allowed else S.FAIL,V.INFO if allowed else V.ERROR,"Symbol whitelist","Allowed symbol whitelist is explicit." if allowed else "Allowed symbol whitelist is empty.",{"allowed_symbols":sorted(allowed)},"Set --allowed-symbols.")]
    for it in trade_intents or []:
        sym=str(_get(it,"symbol","")).upper()
        checks.append(_c(f"symbol_whitelist_{sym}",C.WHITELIST,S.PASS if sym in allowed else S.FAIL,V.INFO if sym in allowed else V.ERROR,"TradeIntent whitelist",f"{sym} is whitelisted." if sym in allowed else f"{sym} is not whitelisted.",{"symbol":sym,"allowed_symbols":sorted(allowed)},"Remove non-whitelisted intent."))
    return checks

def _required(config, flag, obj, scope, cid, title, pass_words=("PASS","APPROVED","ALLOWED","CLOSED","OK","SUCCESS")):
    if not getattr(config, flag): return [_c(cid,scope,S.SKIP,V.INFO,title,f"{flag}=False; skipped.")]
    if obj is None: return [_c(cid,scope,S.FAIL,V.ERROR,title,"Required evidence missing.",{},"Provide required evidence file/report.")]
    txt=_status_text(obj)
    ok=any(w in txt for w in pass_words) or _get(obj,"success",False) is True or _get(obj,"allowed",False) is True
    return [_c(cid,scope,S.PASS if ok else S.FAIL,V.INFO if ok else V.ERROR,title,"Required evidence passed." if ok else f"Required evidence not passing: {txt}",{"status":txt})]

def check_risk_gate_required(config,risk_decisions=None):
    if risk_decisions is not None and isinstance(risk_decisions, Iterable) and not isinstance(risk_decisions,(str,bytes,Mapping)):
        items=list(risk_decisions); ok=bool(items) and all(_get(x,"allowed",False) for x in items)
        return [_c("risk_gate_required",C.RISK,S.PASS if ok else S.FAIL,V.INFO if ok else V.ERROR,"Risk Gate required","All RiskDecision objects allowed." if ok else "Risk Gate evidence missing or blocked.",{"count":len(items)})]
    return _required(config,"require_risk_gate",risk_decisions,C.RISK,"risk_gate_required","Risk Gate required")
def check_human_approval_required(config, approval_status=None): return _required(config,"require_human_approval",approval_status,C.APPROVAL,"human_approval_required","Human Approval required",("APPROVED",))
def check_paper_trading_required(config, paper_status=None): return _required(config,"require_paper_trading",paper_status,C.PAPER,"paper_trading_required","Paper Trading required")
def check_live_readiness_audit_required(config, audit_report=None): return _required(config,"require_live_readiness_audit",audit_report,C.AUDIT,"live_readiness_audit_required","Live Readiness Audit required",("GO","PASS","OK","SUCCESS"))
def check_monitoring_required(config, monitoring_report=None): return _required(config,"require_monitoring",monitoring_report,C.MONITORING,"monitoring_required","Monitoring required",("CLOSED","PASS","OK","SUCCESS"))
def check_agent_research_required(config, agent_memo=None): return _required(config,"require_agent_research",agent_memo,C.AGENT,"agent_research_required","Agent Research required",("PASS","OK","SUCCESS","READ_ONLY"))
def check_circuit_breaker_required(config, circuit_breaker_decision=None):
    if not config.require_circuit_breaker_closed: return [_c("circuit_breaker_required",C.MONITORING,S.SKIP,V.INFO,"Circuit Breaker","Not required.")]
    if circuit_breaker_decision is None: return [_c("circuit_breaker_required",C.MONITORING,S.FAIL,V.ERROR,"Circuit Breaker","Circuit breaker evidence missing.")]
    state=_status_text(circuit_breaker_decision); ok="CLOSED" in state
    return [_c("circuit_breaker_required",C.MONITORING,S.PASS if ok else S.FAIL,V.INFO if ok else V.CRITICAL,"Circuit Breaker",f"Circuit breaker state={state}.",{"state":state},"Wait until circuit breaker is CLOSED.")]
def check_quality_required(config, cache_quality_decision=None):
    if not config.require_quality_pass: return [_c("quality_required",C.SYSTEM,S.SKIP,V.INFO,"Cache quality","Not required.")]
    if cache_quality_decision is None: return [_c("quality_required",C.SYSTEM,S.FAIL,V.ERROR,"Cache quality","Quality evidence missing.")]
    q=_status_text(cache_quality_decision)
    if "PASS" in q or "HIGH" in q: return [_c("quality_required",C.SYSTEM,S.PASS,V.INFO,"Cache quality",f"Quality passed: {q}.",{"quality":q})]
    if "UNKNOWN" in q and config.allow_unknown_quality_for_review: return [_c("quality_required",C.SYSTEM,S.WARN,V.WARNING,"Cache quality",f"Quality UNKNOWN allowed for manual review only: {q}.",{"quality":q})]
    return [_c("quality_required",C.SYSTEM,S.FAIL,V.ERROR,"Cache quality",f"Quality not acceptable: {q}.",{"quality":q})]
def aggregate_live_gray_checks(checks, config):
    checks=list(checks); fail=any(str(c.status)==S.FAIL.value or c.status==S.FAIL for c in checks); crit=any(str(c.severity)==V.CRITICAL.value or c.severity==V.CRITICAL for c in checks)
    if not config.live_enabled or not config.gray_enabled: decision=LiveGrayDecision.NO_GO
    elif fail or crit: decision=LiveGrayDecision.BLOCKED
    else: decision=LiveGrayDecision.READY_FOR_MANUAL_REVIEW
    if config.live_enabled and (fail or crit): decision=LiveGrayDecision.BLOCKED
    return decision
