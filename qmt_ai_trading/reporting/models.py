"""Data contracts for generated reports and dry-run notifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ReportArtifact:
    """Metadata for one report file written from a pipeline result."""

    path: Path | str
    format: str
    title: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationTarget:
    """Dry-run notification destination descriptor.

    The destination is an opaque label only; this stage never reads or sends
    secrets, tokens, account IDs, or webhook URLs.
    """

    channel: str
    enabled: bool = True
    destination: str = "dry-run-placeholder"
    dry_run: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationResult:
    """Result returned by a notification adapter placeholder."""

    channel: str
    success: bool
    dry_run: bool = True
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
