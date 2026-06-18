"""Safety helpers for the read-only dashboard."""

from __future__ import annotations

import re
from pathlib import Path

from .models import DashboardConfig

FORBIDDEN_UI_ACTIONS = ["提交订单", "实盘下单", "绕过风控", "自动批准", "执行交易", "live submit", "place order"]
SENSITIVE_NAMES = ("token", "key", "password", "secret")


class DashboardSafetyError(ValueError):
    """Raised when dashboard safety validation blocks unsafe configuration or HTML."""


def build_default_dashboard_config(
    *,
    output_path: str = "dashboard_stage31/index.html",
    report_dir: str = "reports",
    monitoring_dir: str = "monitoring_reports",
    agent_dir: str = "agent_reports",
    live_gray_dir: str = "live_gray_reports",
    approval_dir: str = "approvals",
    paper_dir: str = "paper_orders",
    cache_quality_dir: str = "qmt_data_quality_reports",
    data_quality_dir: str = "data_quality_tracking",
    include_data_quality_tracking: bool = False,
    notification_dry_run_dir: str = "notification_dryrun",
    include_notification_dry_run: bool = False,
    title: str = "QMT AI Trading Dashboard",
) -> DashboardConfig:
    return DashboardConfig(
        report_dirs={
            "daily_report": report_dir,
            "monitoring": monitoring_dir,
            "agent_research": agent_dir,
            "live_gray": live_gray_dir,
            "approval": approval_dir,
            "paper": paper_dir,
            "cache_quality": cache_quality_dir,
            "data_quality_tracking": data_quality_dir,
            "notification_dry_run": notification_dry_run_dir,
        },
        output_path=output_path,
        include_data_quality_tracking=include_data_quality_tracking,
        data_quality_dir=data_quality_dir,
        include_notification_dry_run=include_notification_dry_run,
        notification_dry_run_dir=notification_dry_run_dir,
        read_only=True,
        metadata={"title": title, "stage": "stage31-ui-dashboard"},
    )


def assert_dashboard_read_only(config: DashboardConfig) -> None:
    if not config.read_only:
        raise DashboardSafetyError("Dashboard blocked: read_only must remain True.")


def _is_sensitive_path(path: str | Path) -> bool:
    parts = [part.lower() for part in Path(path).parts]
    name = Path(path).name.lower()
    if name == ".env" or name.startswith(".env"):
        return True
    return any(term in name or term in "/".join(parts) for term in SENSITIVE_NAMES)


def validate_dashboard_config(config: DashboardConfig) -> None:
    assert_dashboard_read_only(config)
    for key, path in config.report_dirs.items():
        if _is_sensitive_path(path):
            raise DashboardSafetyError(f"Dashboard blocked: report directory for {key} appears sensitive.")
    if _is_sensitive_path(config.output_path):
        raise DashboardSafetyError("Dashboard blocked: output path appears sensitive.")


def sanitize_dashboard_text(text: object) -> str:
    raw = "" if text is None else str(text)
    raw = re.sub(r"(?i)(token|key|password|secret)\s*[:=]\s*([^\s,;\n]+)", r"\1=[REDACTED]", raw)
    raw = re.sub(r"(?i)(token|key|password|secret)[-_ ]?value\s*[:=]\s*([^\s,;\n]+)", r"\1_value=[REDACTED]", raw)
    return raw


def contains_forbidden_ui_action(text: object) -> bool:
    lower = sanitize_dashboard_text(text).lower()
    return any(action.lower() in lower for action in FORBIDDEN_UI_ACTIONS)


def validate_dashboard_html_safety(html: str) -> None:
    lower = html.lower()
    if re.search(r"<button\b", lower) and contains_forbidden_ui_action(lower):
        raise DashboardSafetyError("Dashboard blocked: HTML contains forbidden order/action button.")
    if re.search(r"<(script|iframe)\b", lower):
        raise DashboardSafetyError("Dashboard blocked: script/iframe is not allowed.")
    if re.search(r"https?://|//cdn\.", lower):
        raise DashboardSafetyError("Dashboard blocked: external network/CDN reference is not allowed.")
    if contains_forbidden_ui_action(lower):
        raise DashboardSafetyError("Dashboard blocked: HTML contains forbidden UI action text.")
