from __future__ import annotations

import json, re
from typing import Any, Mapping
from .models import LiveEnvCheckConfig, LiveEnvCheckDecision, LiveEnvCheckReport, SAFETY_NOTE

FORBIDDEN_PATTERNS = [r"--live-enabled", r"--execute-live", r"live_enabled\s*=\s*True", r"real_order_enabled\s*=\s*True", r"xttrader", r"place_order", r"submit_order", r"order_stock", r"real[-_ ]?send", r"requests\.post", r"\bsmtp\b", r"sendMessage", r"webhook", r"自动批准", r"绕过风控", r"直接实盘", r"查询资金", r"查询持仓", r"查询订单", r"查询成交"]
SENSITIVE_KEYS = ("token", "key", "password", "secret", "account", "bearer")

def build_default_live_env_check_config(*, allowed_symbols=None, max_total_capital=5000.0, max_single_order_value=1000.0, max_symbol_weight=0.1, max_portfolio_weight=0.2, operator_name="", reviewer_name="", metadata=None, **overrides: Any) -> LiveEnvCheckConfig:
    cfg = LiveEnvCheckConfig(allowed_symbols=[str(x).strip() for x in (allowed_symbols or []) if str(x).strip()], max_total_capital=max_total_capital, max_single_order_value=max_single_order_value, max_symbol_weight=max_symbol_weight, max_portfolio_weight=max_portfolio_weight, operator_name=operator_name, reviewer_name=reviewer_name, metadata=sanitize_live_env_check_metadata(metadata or {}))
    for k, v in overrides.items():
        if hasattr(cfg, k): setattr(cfg, k, v)
    validate_live_env_check_is_read_only(cfg)
    return cfg

def validate_live_env_check_is_read_only(config: LiveEnvCheckConfig) -> None:
    meta = config.metadata or {}
    for k in ("live_enabled", "real_order_enabled", "real_send_enabled", "external_network_enabled"):
        if bool(meta.get(k, False)):
            raise ValueError(f"forbidden live env flag: {k}")

def contains_forbidden_live_env_action(text: str | None) -> bool:
    value = text or ""
    return any(re.search(p, value, flags=re.IGNORECASE) for p in FORBIDDEN_PATTERNS)

def assert_no_live_execution_flags(text: str | None) -> None:
    value = text or ""
    hits = [p for p in FORBIDDEN_PATTERNS if re.search(p, value, flags=re.IGNORECASE)]
    if hits:
        raise ValueError("Forbidden live execution marker detected: " + ", ".join(hits[:5]))

def _mask_value(value: Any) -> Any:
    if isinstance(value, Mapping): return sanitize_live_env_check_metadata(value)
    if isinstance(value, list): return [_mask_value(v) for v in value]
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    text = str(value)
    text = re.sub(r"sk-[A-Za-z0-9_-]+", "sk-***", text)
    text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._-]+", r"\1***", text)
    return text

def sanitize_live_env_check_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for k, v in dict(metadata or {}).items():
        lk = str(k).lower()
        clean[str(k)] = "***REDACTED***" if any(s in lk for s in SENSITIVE_KEYS) else _mask_value(v)
    return clean

def validate_live_env_check_report_safety(report: LiveEnvCheckReport) -> LiveEnvCheckReport:
    scan_payload = {"checks": [c.to_dict() for c in report.checks], "metadata": report.metadata}
    text = json.dumps(scan_payload, ensure_ascii=False, default=str)
    if contains_forbidden_live_env_action(text):
        report.decision = LiveEnvCheckDecision.BLOCKED
        report.success = False
        if "Forbidden live execution tendency detected in report text." not in report.blocked_reasons:
            report.blocked_reasons.append("Forbidden live execution tendency detected in report text.")
    if not report.safety_note:
        report.safety_note = SAFETY_NOTE
    return report
