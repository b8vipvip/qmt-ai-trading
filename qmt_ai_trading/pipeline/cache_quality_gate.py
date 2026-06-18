"""Stage 25 cache quality gate for cached-real-first pipeline decisions.

This module only reads local cache metadata and local QMT quality reports. It does
not import xtdata/xttrader and never submits orders.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class CacheQualityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"
    UNAVAILABLE = "UNAVAILABLE"


QUALITY_ORDER = {
    CacheQualityLevel.UNAVAILABLE.value: 0,
    CacheQualityLevel.UNKNOWN.value: 1,
    CacheQualityLevel.LOW.value: 1,
    CacheQualityLevel.MEDIUM.value: 2,
    CacheQualityLevel.HIGH.value: 3,
}


@dataclass
class CacheQualityGatePolicy:
    require_quality_report: bool = False
    min_quality_level: str = CacheQualityLevel.UNKNOWN.value
    allow_unknown_quality_for_dry_run: bool = True
    allow_mock_cache: bool = False
    allow_stale_quality_report: bool = True
    max_quality_report_age_hours: float = 72.0
    require_cache_coverage: bool = True
    min_coverage_ratio: float = 0.8
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheQualityGateDecision:
    allowed: bool
    quality_level: str = CacheQualityLevel.UNKNOWN.value
    selected_cache_type: str = "cached_unknown_quality"
    quality_report_path: str | None = None
    quality_report_decision: str | None = None
    coverage_ratio: float = 0.0
    fallback_used: bool = False
    allow_trade_intents: bool = False
    message: str = ""
    remediation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _level(value: str | CacheQualityLevel | None) -> str:
    if isinstance(value, CacheQualityLevel):
        return value.value
    text = str(value or CacheQualityLevel.UNKNOWN.value).upper()
    return text if text in QUALITY_ORDER else CacheQualityLevel.UNKNOWN.value


def build_cache_quality_gate_policy(**kwargs: Any) -> CacheQualityGatePolicy:
    policy = CacheQualityGatePolicy(**kwargs)
    policy.min_quality_level = _level(policy.min_quality_level)
    policy.min_coverage_ratio = max(0.0, min(1.0, float(policy.min_coverage_ratio)))
    policy.max_quality_report_age_hours = max(0.0, float(policy.max_quality_report_age_hours))
    return policy


def load_latest_qmt_quality_report(report_dir: str | Path | None) -> dict[str, Any] | None:
    if not report_dir:
        return None
    root = Path(report_dir)
    if not root.exists() or not root.is_dir():
        return None
    candidates = sorted(root.glob("*.qmt_quality.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        candidates = sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("_path", str(path))
                return data
        except Exception:
            continue
    return None


def _load_report(report_or_path: Mapping[str, Any] | str | Path | None) -> dict[str, Any] | None:
    if report_or_path is None:
        return None
    if isinstance(report_or_path, Mapping):
        return dict(report_or_path)
    path = Path(report_or_path)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data.setdefault("_path", str(path))
        return data
    return None


def classify_cache_quality(report_or_path: Mapping[str, Any] | str | Path | None, coverage_ratio: float | None = None) -> str:
    report = _load_report(report_or_path)
    if not report:
        return CacheQualityLevel.UNKNOWN.value
    decision = str(report.get("decision") or report.get("quality_decision") or "").upper()
    if decision == "PASS":
        if coverage_ratio is not None and float(coverage_ratio) < 0.8:
            return CacheQualityLevel.MEDIUM.value
        return CacheQualityLevel.HIGH.value
    if decision == "WARN":
        return CacheQualityLevel.LOW.value
    if decision in {"SKIP", "SKIPPED", "UNAVAILABLE"}:
        return CacheQualityLevel.UNKNOWN.value if decision.startswith("SKIP") else CacheQualityLevel.UNAVAILABLE.value
    if decision in {"FAIL", "FAILED"}:
        return CacheQualityLevel.LOW.value
    return CacheQualityLevel.UNKNOWN.value


def _is_stale(report: Mapping[str, Any], policy: CacheQualityGatePolicy) -> bool:
    raw = report.get("created_at") or report.get("timestamp")
    if not raw:
        return False
    try:
        created = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - created.astimezone(timezone.utc)).total_seconds() / 3600
        return age_hours > policy.max_quality_report_age_hours
    except Exception:
        return False


def evaluate_cache_quality_gate(
    *,
    coverage_ratio: float = 0.0,
    quality_report: Mapping[str, Any] | str | Path | None = None,
    quality_report_dir: str | Path | None = None,
    policy: CacheQualityGatePolicy | None = None,
    cache_available: bool = True,
    fallback_used: bool = False,
    mock_cache: bool = False,
) -> CacheQualityGateDecision:
    policy = policy or build_cache_quality_gate_policy()
    report = _load_report(quality_report) or load_latest_qmt_quality_report(quality_report_dir)
    path = str(report.get("_path")) if report and report.get("_path") else None
    report_decision = str(report.get("decision") or report.get("quality_decision")) if report else None

    if fallback_used or mock_cache:
        allowed = bool(policy.allow_mock_cache)
        return CacheQualityGateDecision(allowed, CacheQualityLevel.LOW.value, "mock_fallback" if fallback_used else "cached_mock_data", path, report_decision, coverage_ratio, bool(fallback_used), allowed, "mock/fallback cache requires explicit allow_mock_cache and is LOW confidence", "Use real QMT cache with PASS quality report before live decisions.", {"mock_cache": mock_cache})

    if policy.require_cache_coverage and (not cache_available or coverage_ratio < policy.min_coverage_ratio):
        return CacheQualityGateDecision(False, CacheQualityLevel.UNAVAILABLE.value, "cache_unavailable", path, report_decision, coverage_ratio, False, False, "cache coverage is missing or below threshold; no silent mock fallback", "Warm up local cache or explicitly enable mock fallback for dry-run only.")

    if not report:
        if policy.require_quality_report:
            return CacheQualityGateDecision(False, CacheQualityLevel.UNAVAILABLE.value, "blocked_missing_quality", None, None, coverage_ratio, False, False, "quality report is required but missing", "Run stage24 QMT data quality check or disable require_quality_report for dry-run.")
        if policy.allow_unknown_quality_for_dry_run:
            return CacheQualityGateDecision(True, CacheQualityLevel.UNKNOWN.value, "cached_unknown_quality", None, None, coverage_ratio, False, True, "no quality report found; dry-run allowed with UNKNOWN cache quality", "Generate a PASS QMT quality report before live trading decisions.")
        return CacheQualityGateDecision(False, CacheQualityLevel.UNKNOWN.value, "blocked_missing_quality", None, None, coverage_ratio, False, False, "quality is unknown and dry-run unknown quality is disabled", "Enable allow_unknown_quality_for_dry_run or provide quality report.")

    quality = classify_cache_quality(report, coverage_ratio)
    if _is_stale(report, policy) and not policy.allow_stale_quality_report:
        return CacheQualityGateDecision(False, CacheQualityLevel.LOW.value, "stale_quality_report", path, report_decision, coverage_ratio, False, False, "quality report is stale", "Regenerate the QMT quality report.")
    meets = QUALITY_ORDER.get(quality, 0) >= QUALITY_ORDER.get(_level(policy.min_quality_level), 0)
    selected = "cached_real_data" if quality == CacheQualityLevel.HIGH.value else "cached_unknown_quality"
    return CacheQualityGateDecision(meets, quality, selected, path, report_decision, coverage_ratio, False, meets, f"cache quality {quality} from report decision {report_decision}", "Improve cache quality or lower dry-run threshold only for shadow validation.", {"report_id": report.get("report_id")})


def format_cache_quality_gate_decision(decision: CacheQualityGateDecision) -> str:
    lines = [
        "Cache Quality Gate Decision",
        f"allowed={decision.allowed}",
        f"quality_level={decision.quality_level}",
        f"selected_cache_type={decision.selected_cache_type}",
        f"quality_report_path={decision.quality_report_path or ''}",
        f"quality_report_decision={decision.quality_report_decision or ''}",
        f"coverage_ratio={decision.coverage_ratio:.4f}",
        f"fallback_used={decision.fallback_used}",
        f"allow_trade_intents={decision.allow_trade_intents}",
        f"message={decision.message}",
        f"remediation={decision.remediation}",
    ]
    return "\n".join(lines)
