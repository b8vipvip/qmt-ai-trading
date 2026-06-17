"""Report writers for dry-run/shadow daily pipeline results."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Mapping

from qmt_ai_trading.pipeline.models import PipelineResult
from qmt_ai_trading.pipeline.report import format_pipeline_report
from qmt_ai_trading.reporting.models import ReportArtifact

REPORT_TITLE = "QMT AI Trading Daily Signal Report"


def _safe_value(value: Any) -> Any:
    """Convert known pipeline objects to JSON-safe data without secrets."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return _safe_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _safe_value(item) for key, item in value.items() if not _looks_sensitive(str(key))}
    if isinstance(value, (list, tuple, set)):
        return [_safe_value(item) for item in value]
    return str(value)


def _looks_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in ("token", "secret", "password", "passwd", "credential", "account", "api_key", "apikey"))


def _pipeline_payload(result: PipelineResult) -> dict[str, Any]:
    return {
        "title": REPORT_TITLE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "context": _safe_value(result.context),
        "success": result.success,
        "steps": _safe_value(result.steps),
        "research_scores": _safe_value(result.research_scores),
        "candidates": _safe_value(result.candidates),
        "trade_intents": _safe_value(result.trade_intents),
        "risk_decisions": _safe_value(result.risk_decisions),
        "backtest_result": _safe_value(result.backtest_result),
        "shadow_replay_result": _safe_value(result.shadow_replay_result),
        "metadata": _safe_value(result.metadata),
        "safety_note": "Dry-run/shadow report only; not an order instruction.",
    }


def ensure_report_dir(report_dir: str | Path | None = None, *, trade_date: date | str | None = None) -> Path:
    """Create and return the report output directory; default is reports/YYYY-MM-DD/."""

    if report_dir is None:
        day = str(trade_date or date.today())
        path = Path("reports") / day
    else:
        path = Path(report_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_markdown_report(result: PipelineResult, report_dir: str | Path | None = None) -> ReportArtifact:
    directory = ensure_report_dir(report_dir, trade_date=result.context.trade_date)
    path = directory / "daily_report.md"
    text = result.report_text or format_pipeline_report(result)
    path.write_text(text + "\n", encoding="utf-8")
    return ReportArtifact(path=path, format="markdown", title=REPORT_TITLE, metadata={"run_id": result.context.run_id})


def write_json_report(result: PipelineResult, report_dir: str | Path | None = None) -> ReportArtifact:
    directory = ensure_report_dir(report_dir, trade_date=result.context.trade_date)
    path = directory / "daily_report.json"
    path.write_text(json.dumps(_pipeline_payload(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return ReportArtifact(path=path, format="json", title=REPORT_TITLE, metadata={"run_id": result.context.run_id})


def write_html_report(result: PipelineResult, report_dir: str | Path | None = None) -> ReportArtifact:
    directory = ensure_report_dir(report_dir, trade_date=result.context.trade_date)
    path = directory / "daily_report.html"
    markdown = result.report_text or format_pipeline_report(result)
    body = "\n".join(f"<p>{escape(line)}</p>" if line else "<br>" for line in markdown.splitlines())
    html = f"<!doctype html>\n<html><head><meta charset='utf-8'><title>{escape(REPORT_TITLE)}</title></head><body>{body}</body></html>\n"
    path.write_text(html, encoding="utf-8")
    return ReportArtifact(path=path, format="html", title=REPORT_TITLE, metadata={"run_id": result.context.run_id})


def write_pipeline_reports(result: PipelineResult, report_dir: str | Path | None = None) -> list[ReportArtifact]:
    """Write Markdown, JSON, and HTML reports for one pipeline result."""

    directory = ensure_report_dir(report_dir, trade_date=result.context.trade_date)
    return [
        write_markdown_report(result, directory),
        write_json_report(result, directory),
        write_html_report(result, directory),
    ]
