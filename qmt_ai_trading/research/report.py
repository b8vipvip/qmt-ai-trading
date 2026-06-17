"""Human-readable Stage 6 research report helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from qmt_ai_trading.research.scoring import ResearchScore


@dataclass(slots=True)
class ResearchReport:
    title: str
    scores: list[ResearchScore] = field(default_factory=list)
    summary: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    disclaimer: str = "仅作为辅助分析，不构成投资承诺或收益保证。"
    metadata: dict[str, Any] = field(default_factory=dict)


def build_research_report(scores: Iterable[ResearchScore], *, title: str = "Stage 6 Research Summary") -> ResearchReport:
    """Build a structured report from research scores."""

    ranked = sorted(list(scores or []), key=lambda item: (item.score is not None, item.score or 0.0), reverse=True)
    eligible_count = sum(1 for item in ranked if item.eligible)
    summary = f"{len(ranked)} symbols analyzed; {eligible_count} eligible research scores."
    return ResearchReport(title=title, scores=ranked, summary=summary)


def format_research_report_text(report: ResearchReport) -> str:
    """Format a research report as readable text."""

    lines = [report.title, report.summary, report.disclaimer, ""]
    for item in report.scores:
        score_text = "N/A" if item.score is None else f"{item.score:.2f}"
        status = "eligible" if item.eligible else "ineligible"
        reason = f" reason={item.reason}" if item.reason else ""
        lines.append(f"- {item.symbol}: score={score_text}, {status}{reason}")
    return "\n".join(lines).strip()
