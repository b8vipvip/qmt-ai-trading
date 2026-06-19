from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

from .models import RedlineReviewConfig, RedlineReviewDecision, RedlineReviewReport
from .safety import build_default_redline_review_config, sanitize_redline_metadata
from .scanner import aggregate_redline_findings, iter_scan_files, scan_file_for_redline_markers, scan_sensitive_files
from .formatters import format_redline_review_report_json, format_redline_review_report_markdown


def run_redline_review(repo_root: str | Path = ".", **kwargs) -> RedlineReviewReport:
    return run_redline_review_from_repo(repo_root=repo_root, **kwargs)


def run_redline_review_from_repo(repo_root: str | Path = ".", **kwargs) -> RedlineReviewReport:
    config = build_default_redline_review_config(repo_root=str(repo_root), **kwargs)
    root = Path(config.repo_root).resolve()
    findings = []
    for path in iter_scan_files(root, config.include_paths, config.exclude_paths):
        findings.extend(scan_file_for_redline_markers(path, config))
    if config.require_no_sensitive_files:
        findings.extend(scan_sensitive_files(root, config))
    decision, summary, blocked_reasons, warnings = aggregate_redline_findings(findings, config)
    return RedlineReviewReport(
        report_id=f"redline-review-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}",
        created_at=datetime.now(timezone.utc).isoformat(),
        decision=decision,
        config=config,
        findings=findings,
        blocked_reasons=blocked_reasons,
        warnings=warnings,
        summary=summary,
        success=decision != RedlineReviewDecision.BLOCKED,
        message="READY_FOR_REDLINE_REVIEW is not live trading authorization.",
        metadata=sanitize_redline_metadata({"review_only": True}),
    )


def save_redline_review_report(report: RedlineReviewReport, output_path: str | Path, json_output_path: str | Path | None = None) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(format_redline_review_report_markdown(report), encoding="utf-8")
    if json_output_path:
        json_path = Path(json_output_path)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(format_redline_review_report_json(report), encoding="utf-8")


def load_redline_review_report(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

