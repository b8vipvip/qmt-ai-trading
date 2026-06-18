from __future__ import annotations
import json
from .models import SAFETY_NOTE

def format_notification_message(m): return f"### {m.subject}\n- source: {m.source}\n- severity: {getattr(m.severity,'value',m.severity)}\n\n{m.body}\n"
def format_delivery_plan(p): return f"### Plan {p.plan_id}\n- channel: {getattr(p.channel,'value',p.channel)}\n- send_mode: {getattr(p.send_mode,'value',p.send_mode)}\n- dry_run: {p.dry_run}\n- real_send_enabled: {p.real_send_enabled}\n- external_network_enabled: {p.external_network_enabled}\n- recipient: {p.recipient.destination_masked}\n- blocked_reasons: {', '.join(p.blocked_reasons) if p.blocked_reasons else 'None'}\n"
def format_notification_audit(a): return f"## Audit result\n- passed: {a.passed}\n- severity: {getattr(a.severity,'value',a.severity)}\n- blocked_reasons: {', '.join(a.blocked_reasons) if a.blocked_reasons else 'None'}\n- warnings: {', '.join(a.warnings) if a.warnings else 'None'}\n"
def format_notification_dry_run_markdown(r):
    parts=["# Notification dry-run summary", f"- success: {r.success}", f"- messages: {len(r.messages)}", f"- recipients: {len(r.recipients)}", f"- delivery_plans: {len(r.delivery_plans)}", "\n## Messages"]
    parts += [format_notification_message(m) for m in r.messages] or ['No messages.']
    parts += ["\n## Recipients masked"] + [f"- {getattr(x.channel,'value',x.channel)}: {x.destination_masked}" for x in r.recipients]
    parts += ["\n## Delivery plans"] + [format_delivery_plan(p) for p in r.delivery_plans]
    parts += [format_notification_audit(r.audit_result), "\n## Blocked reasons"]
    parts += [f"- {b}" for b in (r.audit_result.blocked_reasons or [])] or ['- None']
    parts += ["\n## Safety note", SAFETY_NOTE]
    return '\n'.join(parts)+"\n"
def format_notification_dry_run_json(r): return json.dumps(r.to_dict(), ensure_ascii=False, indent=2)
