"""Safety checks for gray rehearsal dry-run flows."""
from __future__ import annotations
import re
from typing import Any, Mapping
from .models import GrayRehearsalConfig, GrayRehearsalReport, SAFETY_NOTE

FORBIDDEN = ["--live-enabled","xttrader","place_order","submit_order","order_stock","real_send","requests.post","smtp","sendMessage","webhook","自动批准","绕过风控","直接实盘","查询资金","查询持仓","查询订单","查询成交"]
SENSITIVE_KEYS = ("token","key","password","secret","account","bearer")

def sanitize_gray_rehearsal_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    def clean(k: str, v: Any) -> Any:
        if any(t in k.lower() for t in SENSITIVE_KEYS): return "***REDACTED***"
        if isinstance(v, str):
            v = re.sub(r"(?i)bearer\s+[A-Za-z0-9._-]+", "Bearer ***REDACTED***", v)
            v = re.sub(r"sk-[A-Za-z0-9_-]+", "sk-***REDACTED***", v)
        if isinstance(v, Mapping): return {str(kk): clean(str(kk), vv) for kk,vv in v.items()}
        if isinstance(v, list): return [clean(k, x) for x in v]
        return v
    return {str(k): clean(str(k), v) for k,v in dict(metadata or {}).items()}

def build_default_gray_rehearsal_config(**kwargs: Any) -> GrayRehearsalConfig:
    if "metadata" in kwargs: kwargs["metadata"] = sanitize_gray_rehearsal_metadata(kwargs["metadata"])
    cfg = GrayRehearsalConfig(**kwargs)
    validate_gray_rehearsal_is_dry_run(cfg); assert_no_live_or_real_send(cfg)
    return cfg

def contains_forbidden_gray_rehearsal_action(text: str | None) -> bool:
    lowered = str(text or "")
    return any(term.lower() in lowered.lower() for term in FORBIDDEN)

def validate_gray_rehearsal_is_dry_run(config: GrayRehearsalConfig) -> None:
    if not config.rehearsal_dry_run: raise ValueError("gray rehearsal must remain dry-run only")

def assert_no_live_or_real_send(config: GrayRehearsalConfig) -> None:
    meta = config.metadata or {}
    for key in ("live_enabled","real_send_enabled","external_network_enabled"):
        if bool(meta.get(key, False)): raise ValueError(f"{key} is forbidden for gray rehearsal")

def validate_gray_rehearsal_report_safety(report: GrayRehearsalReport) -> None:
    if SAFETY_NOTE not in report.safety_note: raise ValueError("missing gray rehearsal safety note")
    validate_gray_rehearsal_is_dry_run(report.config)
    if contains_forbidden_gray_rehearsal_action(str(report.metadata)): raise ValueError("forbidden action detected in gray rehearsal report metadata")
