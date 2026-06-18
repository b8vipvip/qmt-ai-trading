"""Dry-run alert writer for Stage 28 monitoring.

This module intentionally writes local JSON files only. It does not send email,
Telegram, WeCom/Enterprise WeChat, or any other real notification.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Alert, MonitoringReport


def write_dry_run_alerts(report: MonitoringReport, output_dir: str | Path | None) -> list[dict[str, object]]:
    alerts: list[dict[str, object]] = []
    if not output_dir:
        return alerts
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    for idx, event in enumerate(report.events, start=1):
        if event.severity == "INFO":
            continue
        alert = Alert(
            run_id=report.run_id,
            severity=event.severity,
            event=event.name,
            message=event.message,
            created_at=report.generated_at,
        )
        path = root / f"{report.run_id}.{idx}.{event.name}.alert.json"
        payload = alert.to_dict()
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["path"] = str(path)
        alerts.append(payload)
    return alerts
