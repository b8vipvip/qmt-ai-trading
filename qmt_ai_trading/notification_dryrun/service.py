from __future__ import annotations
import json
from pathlib import Path
from .audit import audit_notification_report
from .formatters import format_notification_dry_run_json, format_notification_dry_run_markdown
from .models import NotificationChannel, NotificationDryRunReport
from .planner import build_delivery_plans, build_recipients_from_config, save_delivery_plan_preview, suppress_real_channels
from .templates import build_agent_research_message, build_daily_pipeline_summary_message, build_data_quality_tracking_message, build_final_acceptance_message, build_live_gray_readiness_message, build_monitoring_alert_message

BUILDERS={'daily_report':build_daily_pipeline_summary_message,'monitoring_report':build_monitoring_alert_message,'data_quality_report':build_data_quality_tracking_message,'agent_memo':build_agent_research_message,'live_gray_report':build_live_gray_readiness_message,'final_acceptance':build_final_acceptance_message}

def _channels(channels):
    if channels is None: return [NotificationChannel.FILE, NotificationChannel.CONSOLE]
    if isinstance(channels,str): channels=[x.strip() for x in channels.split(',') if x.strip()]
    return [c if isinstance(c,NotificationChannel) else NotificationChannel[str(c).upper()] for c in channels]

def run_notification_dry_run(*, summaries=None, channels=None, recipients=None, output_path=None, json_output_path=None, preview_output_dir=None, metadata=None):
    chans=_channels(channels); messages=[]
    for k,v in (summaries or {}).items():
        b=BUILDERS.get(k, build_daily_pipeline_summary_message); messages.append(b(v, channel=chans[0]))
    rcpts=build_recipients_from_config(recipients, chans)
    plans=suppress_real_channels(build_delivery_plans(messages, rcpts))
    report=NotificationDryRunReport(messages=messages, recipients=rcpts, delivery_plans=plans, metadata=dict(metadata or {}))
    report.audit_result=audit_notification_report(report); report.success=report.audit_result.passed
    report.summary={"messages":len(messages),"recipients":len(rcpts),"delivery_plans":len(plans),"passed":report.audit_result.passed}
    if preview_output_dir: report.output_files += save_delivery_plan_preview(plans, preview_output_dir)
    if output_path: save_notification_dry_run_report(report, output_path); report.output_files.append(str(output_path))
    if json_output_path: save_notification_dry_run_report(report, json_output_path); report.output_files.append(str(json_output_path))
    return report

def run_notification_dry_run_from_files(*, daily_report=None, monitoring_report=None, data_quality_report=None, agent_memo=None, live_gray_report=None, final_acceptance=None, **kw):
    files=locals().copy(); files.pop('kw')
    summaries={}
    for k,p in files.items():
        if p and Path(p).exists(): summaries[k]=Path(p).read_text(encoding='utf-8',errors='replace')
    return run_notification_dry_run(summaries=summaries, **kw)

def save_notification_dry_run_report(report, output_path):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
    text=format_notification_dry_run_json(report) if p.suffix.lower()=='.json' else format_notification_dry_run_markdown(report)
    p.write_text(text, encoding='utf-8'); return p

def load_notification_dry_run_report(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    return data
