"""HTML renderer for the single-file read-only dashboard."""

from __future__ import annotations

import html

from .models import DashboardData, DashboardSection, DashboardStatus, SAFETY_NOTE
from .safety import validate_dashboard_html_safety


def render_dashboard_css() -> str:
    return """
body { font-family: Arial, sans-serif; margin: 0; background: #f6f8fb; color: #1d2733; }
header { background: #182230; color: white; padding: 24px 32px; }
main { padding: 24px 32px; max-width: 1180px; margin: 0 auto; }
.safety { border-left: 6px solid #c2410c; background: #fff7ed; padding: 16px; margin: 20px 0; font-weight: 700; }
.meta, .sources, .warnings { background: white; border: 1px solid #d8dee8; border-radius: 8px; padding: 16px; margin: 16px 0; }
.section { background: white; border: 1px solid #d8dee8; border-radius: 10px; padding: 18px; margin: 18px 0; box-shadow: 0 1px 2px rgba(0,0,0,.04); }
.section h2 { margin-top: 0; display: flex; gap: 10px; align-items: center; }
.badge { border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 700; }
.badge-ok { background: #dcfce7; color: #166534; }
.badge-warning { background: #fef9c3; color: #854d0e; }
.badge-error { background: #fee2e2; color: #991b1b; }
.badge-empty { background: #e5e7eb; color: #374151; }
pre { white-space: pre-wrap; word-break: break-word; background: #0f172a; color: #e2e8f0; padding: 16px; border-radius: 8px; max-height: 460px; overflow: auto; }
small { color: #64748b; }
""".strip()


def render_status_badge(status: DashboardStatus | str) -> str:
    value = status.value if isinstance(status, DashboardStatus) else str(status)
    cls = value.lower() if value in {"OK", "WARNING", "ERROR", "EMPTY"} else "empty"
    return f'<span class="badge badge-{html.escape(cls)}">{html.escape(value)}</span>'


def render_safety_banner() -> str:
    return f'<div class="safety">{html.escape(SAFETY_NOTE)}</div>'


def render_dashboard_section(section: DashboardSection) -> str:
    source = html.escape(section.source_path or "No source file")
    summary = html.escape(section.summary)
    return f"""
<section class="section" id="{html.escape(section.section_id)}">
  <h2>{render_status_badge(section.status)} {html.escape(section.title)}</h2>
  <p>{summary}</p>
  <small>Source: {source}</small>
  <div class="content">{section.html}</div>
</section>
""".strip()


def render_dashboard_html(data: DashboardData) -> str:
    sections = "\n".join(render_dashboard_section(section) for section in data.sections)
    sources = "".join(f"<li>{html.escape(path)}</li>" for path in data.source_paths) or "<li>No local sources loaded.</li>"
    warnings = "".join(f"<li>{html.escape(warning)}</li>" for warning in data.warnings) or "<li>No dashboard warnings.</li>"
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(data.title)}</title>
  <style>{render_dashboard_css()}</style>
</head>
<body>
  <header>
    <h1>{html.escape(data.title)}</h1>
    <p>Generated at: {html.escape(data.generated_at)}</p>
  </header>
  <main>
    {render_safety_banner()}
    <div class="meta"><strong>Mode:</strong> read-only static HTML; no APIs, no order entry, no external scripts.</div>
    <div class="warnings"><h2>Warnings</h2><ul>{warnings}</ul></div>
    {sections}
    <div class="sources"><h2>Source paths</h2><ul>{sources}</ul></div>
  </main>
</body>
</html>
"""
    validate_dashboard_html_safety(document)
    return document
