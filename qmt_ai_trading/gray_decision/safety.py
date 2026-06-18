from __future__ import annotations
import re
from typing import Any, Mapping
from .models import GrayDecision, GrayDecisionConfig, GrayDecisionPackage
FORBIDDEN=["--live-enabled","xttrader","place_order","submit_order","order_stock","real_send","requests.post","smtp","sendmessage","webhook","自动批准","绕过风控","直接实盘","查询资金","查询持仓","查询订单","查询成交"]
SENSITIVE=re.compile(r"(token|key|password|secret|account|bearer|sk-)[^,;\s]*", re.I)
def build_default_gray_decision_config(**kw: Any)->GrayDecisionConfig:
    md=sanitize_gray_decision_metadata(kw.pop("metadata",{}) or {}); md.update({"manual_only":True,"dry_run":True,"live_enabled":False,"real_send_enabled":False,"external_network_enabled":False})
    return GrayDecisionConfig(metadata=md, **kw)
def contains_forbidden_gray_decision_action(text: str|None)->bool:
    t=(text or "").lower(); return any(x.lower() in t for x in FORBIDDEN)
def assert_no_live_execution_flags(text: str|None)->None:
    if contains_forbidden_gray_decision_action(text): raise ValueError("Forbidden live execution or notification action detected in gray decision package input.")
def sanitize_gray_decision_metadata(metadata: Mapping[str,Any]|None)->dict[str,Any]:
    out={}
    for k,v in dict(metadata or {}).items():
        ks=str(k); val="***REDACTED***" if SENSITIVE.search(ks) or SENSITIVE.search(str(v)) else v
        out[ks]=val
    return out
def validate_gray_decision_is_manual_only(config: GrayDecisionConfig)->None:
    text=str(config.to_dict()).lower()
    if "'live_enabled': true" in text or '"live_enabled": true' in text or "real_send_enabled': true" in text: raise ValueError("Gray decision package must remain manual-only and dry-run.")
def validate_gray_decision_package_safety(package: GrayDecisionPackage)->GrayDecisionPackage:
    validate_gray_decision_is_manual_only(package.config)
    scan_parts=[]
    for ev in package.evidence:
        scan_parts.extend([str(ev.summary), str(ev.blocked_reason), str(ev.source_path), str(ev.metadata)])
    scan_parts.extend([str(package.metadata), " ".join(package.blocked_reasons), " ".join(package.warnings), package.summary, package.message])
    text=" ".join(scan_parts)
    if contains_forbidden_gray_decision_action(text):
        package.decision=GrayDecision.BLOCKED; package.success=False
        reason="Forbidden live execution / notification / account-query wording detected; package blocked."
        if reason not in package.blocked_reasons: package.blocked_reasons.append(reason)
    package.safety_note=package.safety_note or "Gray decision package is manual-only and dry-run. It does not enable live trading, does not submit orders, does not send real notifications, and does not call xttrader or QMT trading APIs."
    package.metadata=sanitize_gray_decision_metadata(package.metadata)
    return package
