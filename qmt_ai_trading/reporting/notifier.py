"""Dry-run notification adapter placeholders for generated reports."""

from __future__ import annotations

from typing import Iterable

from qmt_ai_trading.reporting.models import NotificationResult, NotificationTarget, ReportArtifact


def _dry_run_result(channel: str, enabled: bool = True) -> NotificationResult:
    if not enabled:
        return NotificationResult(channel=channel, success=True, dry_run=True, message=f"{channel} notification disabled; no message sent.")
    return NotificationResult(channel=channel, success=True, dry_run=True, message=f"{channel} notification dry-run only; no external service called.")


def notify_email(artifacts: Iterable[ReportArtifact] | None = None, *, target: NotificationTarget | None = None, dry_run: bool = True) -> NotificationResult:
    """Email notification placeholder; never sends in Stage 10."""

    _ = list(artifacts or [])
    resolved = target or NotificationTarget(channel="email", dry_run=True)
    return _dry_run_result("email", enabled=resolved.enabled and dry_run)


def notify_telegram(artifacts: Iterable[ReportArtifact] | None = None, *, target: NotificationTarget | None = None, dry_run: bool = True) -> NotificationResult:
    """Telegram notification placeholder; never connects in Stage 10."""

    _ = list(artifacts or [])
    resolved = target or NotificationTarget(channel="telegram", dry_run=True)
    return _dry_run_result("telegram", enabled=resolved.enabled and dry_run)


def notify_wecom(artifacts: Iterable[ReportArtifact] | None = None, *, target: NotificationTarget | None = None, dry_run: bool = True) -> NotificationResult:
    """WeCom notification placeholder; never connects in Stage 10."""

    _ = list(artifacts or [])
    resolved = target or NotificationTarget(channel="wecom", dry_run=True)
    return _dry_run_result("wecom", enabled=resolved.enabled and dry_run)


def notify_report(artifacts: Iterable[ReportArtifact] | None = None, *, dry_run: bool = True, targets: Iterable[NotificationTarget] | None = None) -> list[NotificationResult]:
    """Notify configured channels in dry-run mode only."""

    artifact_list = list(artifacts or [])
    target_list = list(targets or [NotificationTarget("email"), NotificationTarget("telegram"), NotificationTarget("wecom")])
    results: list[NotificationResult] = []
    for target in target_list:
        channel = target.channel.lower()
        if channel == "email":
            results.append(notify_email(artifact_list, target=target, dry_run=True))
        elif channel == "telegram":
            results.append(notify_telegram(artifact_list, target=target, dry_run=True))
        elif channel in {"wecom", "wechat_work", "enterprise_wechat"}:
            results.append(notify_wecom(artifact_list, target=target, dry_run=True))
        else:
            results.append(NotificationResult(channel=target.channel, success=True, dry_run=True, message="unsupported channel placeholder; no message sent."))
    return results
