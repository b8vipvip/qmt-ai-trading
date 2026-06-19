from __future__ import annotations
import json
from .models import RedlineFinding, RedlineReviewReport, SAFETY_NOTE

def format_redline_finding(f: RedlineFinding)->str:
    return f"| {f.finding_id} | {getattr(f.category,'value',f.category)} | {getattr(f.status,'value',f.status)} | {getattr(f.severity,'value',f.severity)} | {f.path} | {f.line_number or ''} | `{f.marker}` | {f.message} |"

def format_redline_review_report_json(report: RedlineReviewReport)->str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

def format_redline_review_report_markdown(report: RedlineReviewReport)->str:
    critical=[f for f in report.findings if str(getattr(f.status,'value',f.status))=='FAIL' or str(getattr(f.severity,'value',f.severity))=='CRITICAL']
    warnings=[f for f in report.findings if str(getattr(f.status,'value',f.status))=='WARN']
    lines=["# Live switch isolation and red-line review summary","",f"Report ID: `{report.report_id}`",f"Created at: `{report.created_at}`","","## Decision",str(getattr(report.decision,'value',report.decision)),"","## Summary",report.summary, json.dumps(report.metadata.get('aggregate',{}), ensure_ascii=False),"","## Critical blockers"]
    lines += [f"- {b}" for b in report.blocked_reasons] or ["- None detected in checked scope."]
    lines += ["","## Warnings"] + ([f"- {w}" for w in report.warnings] or ["- None."])
    lines += ["","## Findings table","| ID | Category | Status | Severity | Path | Line | Marker | Message |","|---|---|---|---|---|---:|---|---|"]
    lines += [format_redline_finding(f) for f in report.findings] or ["| - | SYSTEM | PASS | INFO | - | - | - | No findings. |"]
    for h,body in [("Scheduler isolation","Scheduler/register previews must remain dry-run only and must not include execute-live entries."),("Dashboard isolation","Dashboard is read-only and must not expose order buttons or live execution controls."),("QMT / xttrader boundary","No xttrader or QMT trading API calls are authorized by this report."),("Notification boundary","No real notification sending is enabled; notification evidence remains dry-run only."),("Account query boundary","No real account/fund/position/order/trade queries are authorized."),("Runtime artifacts / sensitive files","Runtime outputs and sensitive files are excluded or flagged without reading secret contents."),("Manual review checklist","Human reviewers must inspect all blockers/warnings before a separate future stage."),("Safety note",report.safety_note or SAFETY_NOTE),("Next separate stage","阶段四十一：极小资金灰度实盘前只读确认台账（仍不执行）。")]:
        lines += ["",f"## {h}",body]
    return "\n".join(lines)+"\n"
