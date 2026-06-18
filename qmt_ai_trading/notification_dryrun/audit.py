from __future__ import annotations
from .models import NotificationAuditResult, NotificationSeverity
from .safety import contains_sensitive_secret, contains_real_send_action, validate_delivery_plan_safety

def _res(blocked,warnings=None,checks=None):
    return NotificationAuditResult(passed=not blocked, severity=NotificationSeverity.ERROR if blocked else NotificationSeverity.INFO, checks=checks or [], blocked_reasons=blocked, warnings=warnings or [])

def audit_notification_message(message):
    blocked=[]; text=f"{message.subject}\n{message.body}"
    if contains_sensitive_secret(text): blocked.append('message contains sensitive secret pattern')
    if contains_real_send_action(text): blocked.append('message contains real send action pattern')
    return _res(blocked, checks=[{"name":"message_safety","passed":not blocked}])

def audit_recipient(recipient):
    blocked=[]
    if not getattr(recipient,'destination_masked',''): blocked.append('recipient destination is empty')
    if contains_sensitive_secret(recipient.destination_masked): blocked.append('recipient destination contains sensitive pattern')
    return _res(blocked, checks=[{"name":"recipient_masked","passed":not blocked}])

def audit_delivery_plan(plan):
    v=validate_delivery_plan_safety(plan); return _res(list(v['blocked_reasons']), checks=[{"name":"delivery_plan_safety","passed":v['passed']}])

def audit_delivery_plans(plans):
    blocked=[]; checks=[]
    for p in plans:
        a=audit_delivery_plan(p); blocked+=a.blocked_reasons; checks+=a.checks
    # suppressed real channels are expected, not audit failure
    blocked=[b for b in blocked if 'suppressed' not in b]
    return _res(blocked, checks=checks)

def audit_notification_report(report):
    return audit_delivery_plans(getattr(report,'delivery_plans',[]))
