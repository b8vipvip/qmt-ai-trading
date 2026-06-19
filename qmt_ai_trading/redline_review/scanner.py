from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import RedlineCategory, RedlineFinding, RedlineReviewConfig, RedlineReviewDecision, RedlineSeverity, RedlineStatus
from .safety import build_default_redline_review_config, classify_marker, default_forbidden_markers


def _norm(path: str | Path) -> str:
    return str(path).replace("\\", "/").lower()


def _excluded(path: Path, root: Path, config: RedlineReviewConfig) -> bool:
    rel = _norm(path.relative_to(root) if path.is_absolute() else path)
    for part in config.exclude_paths:
        p = part.lower().replace("\\", "/").strip("/")
        if rel == p or rel.startswith(p + "/") or ("/" + p + "/") in ("/" + rel + "/"):
            return True
    return False


def iter_scan_files(repo_root: str | Path, include_paths: list[str] | None = None, exclude_paths: list[str] | None = None) -> Iterable[Path]:
    root = Path(repo_root).resolve()
    config = build_default_redline_review_config(root)
    if include_paths is not None:
        config.include_paths = include_paths
    if exclude_paths is not None:
        config.exclude_paths = exclude_paths
    for include in config.include_paths:
        base = (root / include).resolve()
        if not base.exists():
            continue
        candidates = [base] if base.is_file() else base.rglob("*")
        for path in candidates:
            if not path.is_file() or _excluded(path, root, config):
                continue
            if path.suffix.lower() not in {".py", ".md", ".txt", ".ps1", ".cmd", ".json", ".yaml", ".yml"}:
                continue
            yield path


def scan_text_for_redline_markers(text: str, path: str | Path, config: RedlineReviewConfig | None = None) -> list[RedlineFinding]:
    config = config or build_default_redline_review_config()
    findings: list[RedlineFinding] = []
    markers = default_forbidden_markers()
    for line_number, line in enumerate(text.splitlines(), start=1):
        for marker in markers:
            if marker in line:
                finding = classify_marker(marker, path, line)
                finding.finding_id = f"redline-{len(findings)+1:06d}"
                finding.line_number = line_number
                findings.append(finding)
    return findings


def scan_file_for_redline_markers(path: str | Path, config: RedlineReviewConfig | None = None) -> list[RedlineFinding]:
    path = Path(path)
    config = config or build_default_redline_review_config()
    if not path.exists():
        return [RedlineFinding("missing-file", RedlineCategory.SYSTEM, RedlineStatus.WARN, RedlineSeverity.WARN, path=str(path), message="File missing during red-line scan.", remediation="Confirm whether this file is expected.")]
    if path.stat().st_size > 2_000_000:
        return [RedlineFinding("large-file-skipped", RedlineCategory.SYSTEM, RedlineStatus.SKIPPED, RedlineSeverity.WARN, path=str(path), message="Large file skipped during red-line scan.", remediation="Review manually if needed.")]
    text = path.read_text(encoding="utf-8", errors="replace")
    return scan_text_for_redline_markers(text, path, config)


def scan_scheduler_preview_text(text: str, config: RedlineReviewConfig | None = None) -> list[RedlineFinding]:
    config = config or build_default_redline_review_config()
    findings = scan_text_for_redline_markers(text, "scheduler-preview.txt", config)
    for finding in findings:
        if finding.marker in {"--execute-live", "--live-enabled", "--real-send"}:
            finding.status = RedlineStatus.FAIL
            finding.severity = RedlineSeverity.CRITICAL
            finding.message = f"Scheduler preview contains forbidden execution switch {finding.marker}."
        elif finding.marker == "--execute" and "DRY-RUN ONLY" not in text and "no task registered" not in text:
            finding.status = RedlineStatus.FAIL
            finding.severity = RedlineSeverity.CRITICAL
            finding.message = "Scheduler preview may register a real task without dry-run confirmation."
        else:
            finding.status = RedlineStatus.WARN
            finding.severity = RedlineSeverity.WARN
    return findings


def scan_dashboard_for_order_entry(path_or_text: str | Path, config: RedlineReviewConfig | None = None) -> list[RedlineFinding]:
    if isinstance(path_or_text, (str, Path)) and Path(path_or_text).exists():
        text = Path(path_or_text).read_text(encoding="utf-8", errors="replace")
        path = str(path_or_text)
    else:
        text = str(path_or_text)
        path = "dashboard-text"
    findings = []
    lowered = text.lower()
    for marker in ["submit order", "execute live", "place_order", "order_stock"]:
        if marker in lowered:
            findings.append(RedlineFinding(f"dashboard-{len(findings)+1}", RedlineCategory.DASHBOARD, RedlineStatus.FAIL, RedlineSeverity.CRITICAL, path=path, marker=marker, message=f"Dashboard contains order-entry marker '{marker}'.", remediation="Remove order-entry UI from dashboard."))
    return findings


def scan_sensitive_files(repo_root: str | Path, config: RedlineReviewConfig | None = None) -> list[RedlineFinding]:
    root = Path(repo_root)
    findings: list[RedlineFinding] = []
    for name in [".env", "token.txt", "secrets.json", "credentials.json"]:
        path = root / name
        if path.exists():
            findings.append(RedlineFinding(f"sensitive-{len(findings)+1}", RedlineCategory.SENSITIVE_FILE, RedlineStatus.FAIL, RedlineSeverity.CRITICAL, path=str(path), marker=name, message=f"Sensitive file {name} exists in repository root.", remediation="Move sensitive file outside the repository and keep it ignored."))
    return findings


def aggregate_redline_findings(findings: list[RedlineFinding], config: RedlineReviewConfig | None = None):
    critical = [f for f in findings if str(f.status).endswith("FAIL") or str(f.severity).endswith("CRITICAL")]
    warnings = [f for f in findings if str(f.status).endswith("WARN") or str(f.severity).endswith("WARN")]
    summary = {"total_findings": len(findings), "critical": len(critical), "warnings": len(warnings), "ready_for_redline_review_not_trade_authorization": True}
    if critical:
        return RedlineReviewDecision.BLOCKED, summary, [f"{f.path}:{f.line_number} {f.marker} {f.message}" for f in critical[:50]], [f"{f.path}:{f.line_number} {f.marker}" for f in warnings[:50]]
    return RedlineReviewDecision.READY_FOR_REDLINE_REVIEW, summary, [], [f"{f.path}:{f.line_number} {f.marker}" for f in warnings[:50]]
