from __future__ import annotations
import re
from typing import Any, Mapping
from .models import LiveManualPrepConfig, LiveManualPrepDecision, LiveManualPrepPackage, SAFETY_NOTE
FORBIDDEN=["--live-enabled","--execute-live","live_enabled=True","real_order_enabled=True","xttrader","place_order","submit_order","order_stock","real_send","requests.post","smtp","sendMessage","webhook","自动批准","绕过风控","直接实盘","查询资金","查询持仓","查询订单","查询成交"]
SENSITIVE=re.compile(r"(token|key|password|secret|account|bearer|sk-)[^,;\s]*", re.I)
def build_default_live_manual_prep_config(**kw: Any)->LiveManualPrepConfig:
    md=sanitize_live_manual_prep_metadata(kw.pop("metadata",{}) or {}); md.update({"preparation_only":True,"dry_run":True,"live_enabled":False,"real_order_enabled":False,"real_send_enabled":False,"external_network_enabled":False})
    return LiveManualPrepConfig(metadata=md, **kw)
def contains_forbidden_live_manual_action(text: str|None)->bool:
    t=text or ""; tl=t.lower(); return any(x.lower() in tl for x in FORBIDDEN)
def contains_forbidden_live_manual_prep_action(text: str|None)->bool: return contains_forbidden_live_manual_action(text)
def assert_no_live_execution_flags(text: str|None)->None:
    if contains_forbidden_live_manual_action(text): raise ValueError("Forbidden live execution, account-query, or real-send action detected.")
def sanitize_live_manual_prep_metadata(metadata: Mapping[str,Any]|None)->dict[str,Any]:
    out={}
    for k,v in dict(metadata or {}).items():
        out[str(k)]="***REDACTED***" if SENSITIVE.search(str(k)) or SENSITIVE.search(str(v)) else v
    return out
def validate_live_manual_prep_is_closed_by_default(config: LiveManualPrepConfig)->None:
    text=str(config.to_dict())
    if "'live_enabled': True" in text or "'real_order_enabled': True" in text or "'real_send_enabled': True" in text:
        raise ValueError("Live manual approval prep must remain closed by default.")
def validate_live_manual_prep_is_manual_only(config: LiveManualPrepConfig)->None: validate_live_manual_prep_is_closed_by_default(config)
def validate_live_manual_prep_package_safety(package: LiveManualPrepPackage)->LiveManualPrepPackage:
    validate_live_manual_prep_is_closed_by_default(package.config)
    text=" ".join([str(package.metadata), package.summary, package.message, " ".join(package.blocked_reasons), " ".join(package.warnings)] + [f"{e.summary} {e.blocked_reason} {e.metadata}" for e in package.evidence])
    if contains_forbidden_live_manual_action(text):
        package.decision=LiveManualPrepDecision.BLOCKED; package.success=False
        reason="Forbidden live execution / real notification / account-query wording detected; package blocked."
        if reason not in package.blocked_reasons: package.blocked_reasons.append(reason)
    package.safety_note=SAFETY_NOTE
    package.metadata=sanitize_live_manual_prep_metadata(package.metadata)
    return package
