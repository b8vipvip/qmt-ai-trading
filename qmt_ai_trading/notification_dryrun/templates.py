from __future__ import annotations
from typing import Any
from .models import NotificationChannel, NotificationMessage, NotificationSeverity
from .safety import sanitize_notification_text

def _body(title, content):
    if isinstance(content, dict):
        lines=[f"- {k}: {v}" for k,v in content.items()]
        content='\n'.join(lines)
    return sanitize_notification_text(f"# {title}\n\n{content or 'No local report content provided.'}\n\nDry-run preview only; no real notification was sent.")

def build_generic_report_message(title: str, report_text: str | dict | None = None, *, source='generic', channel=NotificationChannel.FILE, run_id='', severity=NotificationSeverity.INFO, metadata=None):
    return NotificationMessage(channel=channel, severity=severity, subject=sanitize_notification_text(f"[DRY-RUN] {title}"), body=_body(title, report_text), source=source, run_id=run_id, metadata=dict(metadata or {}))

def build_daily_pipeline_summary_message(summary=None, **kw): return build_generic_report_message('Daily Pipeline Summary', summary, source='daily_pipeline', **kw)
def build_monitoring_alert_message(summary=None, **kw): return build_generic_report_message('Monitoring Alert Summary', summary, source='monitoring', severity=kw.pop('severity', NotificationSeverity.WARNING), **kw)
def build_data_quality_tracking_message(summary=None, **kw): return build_generic_report_message('Data Quality Tracking Summary', summary, source='data_quality_tracking', **kw)
def build_agent_research_message(summary=None, **kw): return build_generic_report_message('Agent Research Summary', summary, source='agent_research', **kw)
def build_live_gray_readiness_message(summary=None, **kw): return build_generic_report_message('Live Gray Readiness Summary', summary, source='live_gray_readiness', **kw)
def build_final_acceptance_message(summary=None, **kw): return build_generic_report_message('Final Acceptance Summary', summary, source='final_acceptance', **kw)
