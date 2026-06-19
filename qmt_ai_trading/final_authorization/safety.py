from __future__ import annotations
import re
from typing import Any, Mapping
from .models import FinalAuthorizationConfig, FinalAuthorizationDecision, FinalAuthorizationPackage, SAFETY_NOTE
FORBIDDEN=["--live-enabled","--execute-live","live_enabled=True","real_order_enabled=True","xttrader","place_order","submit_order","order_stock","real_send","requests.post","smtp","sendMessage","webhook","自动批准","绕过风控","直接实盘","查询资金","查询持仓","查询订单","查询成交"]
SENSITIVE=re.compile(r"(token|key|password|secret|account|bearer|sk-)[^,;\s]*", re.I)
def sanitize_final_authorization_metadata(metadata: Mapping[str,Any]|None)->dict[str,Any]:
    return {str(k):("***REDACTED***" if SENSITIVE.search(str(k)) or SENSITIVE.search(str(v)) else v) for k,v in dict(metadata or {}).items()}
def build_default_final_authorization_config(**kw: Any)->FinalAuthorizationConfig:
    md=sanitize_final_authorization_metadata(kw.pop("metadata",{}) or {}); md.update({"final_authorization_dry_run":True,"dry_run":True,"live_enabled":False,"real_order_enabled":False,"real_send_enabled":False,"external_network_enabled":False})
    return FinalAuthorizationConfig(metadata=md, **kw)
def contains_forbidden_final_authorization_action(text: str|None)->bool:
    tl=(text or "").lower(); return any(x.lower() in tl for x in FORBIDDEN)
def assert_no_live_execution_flags(text: str|None)->None:
    if contains_forbidden_final_authorization_action(text): raise ValueError("Forbidden live execution, account-query, or real-send action detected.")
def validate_final_authorization_is_review_only(config: FinalAuthorizationConfig)->None:
    md=config.metadata or {}
    if md.get("live_enabled") is True or md.get("real_order_enabled") is True or md.get("real_send_enabled") is True or md.get("external_network_enabled") is True:
        raise ValueError("Final authorization package must remain review-only and dry-run.")
def validate_final_authorization_package_safety(package: FinalAuthorizationPackage)->FinalAuthorizationPackage:
    validate_final_authorization_is_review_only(package.config)
    text=" ".join([str(package.metadata), package.summary, package.message, " ".join(package.blocked_reasons), " ".join(package.warnings)] + [f"{e.summary} {e.blocked_reason} {e.metadata}" for e in package.evidence])
    if contains_forbidden_final_authorization_action(text):
        package.decision=FinalAuthorizationDecision.BLOCKED; package.success=False
        reason="Forbidden live execution / real notification / account-query wording detected; package blocked."
        if reason not in package.blocked_reasons: package.blocked_reasons.append(reason)
    package.safety_note=SAFETY_NOTE; package.metadata=sanitize_final_authorization_metadata(package.metadata)
    return package
