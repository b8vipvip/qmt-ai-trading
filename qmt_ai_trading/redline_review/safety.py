from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import (
    RedlineCategory,
    RedlineFinding,
    RedlineReviewConfig,
    RedlineSeverity,
    RedlineStatus,
)


def build_default_redline_review_config(repo_root: str | Path = ".", **kwargs: Any) -> RedlineReviewConfig:
    data = RedlineReviewConfig(repo_root=str(repo_root))
    for key, value in kwargs.items():
        if value is not None and hasattr(data, key):
            setattr(data, key, value)
    return data


def sanitize_redline_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        lowered = str(key).lower()
        text = str(value)
        if any(word in lowered for word in ("token", "key", "password", "secret", "account", "bearer")):
            out[key] = "***REDACTED***"
        elif "sk-" in text:
            out[key] = text.replace("sk-", "sk-***")
        else:
            out[key] = value
    return out


def default_forbidden_markers() -> list[str]:
    return [
        "--live-enabled", "--execute-live", "--real-send",
        "live_enabled=True", "execute_live=True", "real_order_enabled=True", "real_send=True",
        "xttrader", "place_order", "submit_order", "order_stock",
        "query_stock_asset", "query_stock_positions", "query_stock_orders", "query_stock_trades",
        "查询资金", "查询持仓", "查询订单", "查询成交",
        "requests.post", "smtp", "sendMessage", "webhook",
        "自动批准", "自动approve", "绕过风控",
        "bypass Risk Gate", "bypass Human Approval",
        "auto live", "auto approve", "auto submit",
        "--execute",
    ]


def default_allowed_context_markers() -> list[str]:
    return [
        "forbidden", "blocked", "blocker", "deny", "reject", "scan", "detect",
        "禁止", "不允许", "不得", "不能", "不会", "不调用", "不下单", "不真实", "不查询",
        "does not", "do not", "no real", "dry-run", "dry_run", "review-only", "read-only",
        "preparation-only", "manual-only", "safety_note", "safety note",
        "default_forbidden_markers", "FORBIDDEN", "forbidden_markers",
        "controlled boundary", "boundary", "gateway", "paper", "audit", "quality",
    ]


CONTROLLED_BOUNDARY_PATHS = (
    "qmt_ai_trading/gateway/",
    "qmt_ai_trading/paper/",
    "qmt_ai_trading/audit/",
    "qmt_ai_trading/datahub/",
    "qmt_ai_trading/redline_review/",
    "scripts/approval_cli.py",
    "scripts/paper_trading_cli.py",
    "scripts/check_qmt_cache_quality.py",
)


def _norm_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").lower()


def _line_is_definition_or_literal(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("#"):
        return True
    if stripped.startswith(("def ", "class ")):
        return True
    if " = [" in stripped or " = (" in stripped:
        return True
    if stripped.startswith(("return [", "return (")):
        return True
    if stripped.endswith(",") and (stripped.startswith('"') or stripped.startswith("'")):
        return True
    return False


def _path_is_docs_or_tests(path: str | Path) -> bool:
    p = _norm_path(path)
    return "/docs/" in p or p.startswith("docs/") or "/tests/" in p or p.startswith("tests/") or p.endswith(".md")


def _path_is_redline_self(path: str | Path) -> bool:
    return "/redline_review/" in _norm_path(path)


def _path_is_safety_or_model(path: str | Path) -> bool:
    p = _norm_path(path)
    name = Path(p).name
    return name in {"safety.py", "models.py", "checks.py"} or "/redline_review/" in p


def _path_is_controlled_boundary(path: str | Path) -> bool:
    p = _norm_path(path)
    return any(marker in p for marker in CONTROLLED_BOUNDARY_PATHS)


def _has_allowed_context(line: str) -> bool:
    lower = line.lower()
    return any(marker.lower() in lower for marker in default_allowed_context_markers())


def marker_category(marker: str) -> RedlineCategory:
    m = marker.lower()
    if "xttrader" in m:
        return RedlineCategory.XTTRADER
    if "query_stock" in m or "查询" in marker:
        return RedlineCategory.ACCOUNT_QUERY
    if any(x in m for x in ("place_order", "submit_order", "order_stock")):
        return RedlineCategory.ORDER_SUBMISSION
    if any(x in m for x in ("requests.post", "smtp", "sendmessage", "webhook", "real-send", "real_send")):
        return RedlineCategory.REAL_NOTIFICATION
    if "execute" in m:
        return RedlineCategory.EXECUTE_SWITCH
    if "live" in m:
        return RedlineCategory.LIVE_SWITCH
    if "risk" in m or "风控" in marker:
        return RedlineCategory.RISK_BYPASS
    if "approval" in m or "approve" in m or "批准" in marker:
        return RedlineCategory.APPROVAL_BYPASS
    return RedlineCategory.SYSTEM


def is_actual_execution_context(marker: str, path: str | Path, line_text: str) -> bool:
    line = line_text.strip()
    lower = line.lower()

    if _path_is_docs_or_tests(path) or _path_is_redline_self(path):
        return False

    # Existing gateway/paper/audit/datahub modules and CLI wrappers are controlled boundaries/evidence in Stage40.
    # They are recorded as WARN but are not considered Stage40 live execution.
    if _path_is_controlled_boundary(path):
        return False

    if _path_is_safety_or_model(path) and (_line_is_definition_or_literal(line) or _has_allowed_context(line)):
        return False
    if _has_allowed_context(line):
        return False
    if _line_is_definition_or_literal(line):
        return False

    if marker == "xttrader":
        return "import xttrader" in lower or "from xtquant import xttrader" in lower or "xttrader." in lower
    if marker in {"place_order", "submit_order", "order_stock", "query_stock_asset", "query_stock_positions", "query_stock_orders", "query_stock_trades"}:
        return f"{marker}(" in line and not line.startswith("def ")
    if marker in {"requests.post", "sendMessage"}:
        return f"{marker}(" in line
    if marker == "smtp":
        return "smtplib.smtp" in lower or ".sendmail(" in lower
    if marker == "webhook":
        return "requests.post" in lower or ".post(" in lower
    if marker in {"--live-enabled", "--execute-live", "--real-send", "--execute"}:
        return False
    if marker in {"live_enabled=True", "execute_live=True", "real_order_enabled=True", "real_send=True"}:
        return marker in line and "False" not in line
    if marker in {"bypass Risk Gate", "bypass Human Approval", "auto live", "auto approve", "auto submit", "自动批准", "自动approve", "绕过风控"}:
        return not _has_allowed_context(line)
    return False


def classify_marker(marker: str, path: str | Path, line_text: str) -> RedlineFinding:
    category = marker_category(marker)
    if is_actual_execution_context(marker, path, line_text):
        status = RedlineStatus.FAIL
        severity = RedlineSeverity.CRITICAL
        message = f"Detected executable red-line marker '{marker}'."
        remediation = "Remove or isolate this execution path behind future explicit human authorization and dry-run guards."
    else:
        status = RedlineStatus.WARN
        severity = RedlineSeverity.WARN
        message = f"Recorded red-line marker '{marker}' in non-execution or controlled-boundary context."
        remediation = "Keep as documentation/test/safety/controlled-boundary marker; no Stage40 live execution detected."

    return RedlineFinding(
        finding_id="classified-marker",
        category=category,
        status=status,
        severity=severity,
        path=str(path),
        line_number=0,
        marker=marker,
        message=message,
        remediation=remediation,
    )


def validate_redline_review_report_safety(report: Any) -> Any:
    findings = getattr(report, "findings", []) or []
    critical = [
        f for f in findings
        if str(getattr(f, "severity", "")).endswith("CRITICAL") or str(getattr(f, "status", "")).endswith("FAIL")
    ]
    if critical:
        report.decision = "BLOCKED"
        report.success = False
        report.blocked_reasons = [getattr(f, "message", "critical red-line finding") for f in critical[:20]]
    return report
