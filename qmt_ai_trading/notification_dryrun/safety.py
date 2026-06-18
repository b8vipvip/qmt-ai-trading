from __future__ import annotations
import re
from typing import Any
from .models import SAFETY_NOTE

SENSITIVE_PATTERNS=[r'(?i)token\s*[:=]',r'(?i)api[_-]?key\s*[:=]',r'(?i)password\s*[:=]',r'(?i)secret\s*[:=]',r'(?i)account\s*[:=]',r'(?i)bearer\s+[a-z0-9._-]+',r'sk-[A-Za-z0-9_-]{8,}']
REAL_SEND_PATTERNS=[r'(?i)real\s*send',r'(?i)smtp',r'(?i)sendMessage',r'(?i)wechat.*webhook',r'(?i)external\s*api',r'(?i)requests\.post',r'(?i)urllib',r'(?i)telegram.*bot']

def build_default_notification_safety_policy():
    return {"dry_run": True, "real_send_enabled": False, "external_network_enabled": False, "safety_note": SAFETY_NOTE}

def contains_sensitive_secret(text: str | None) -> bool:
    t=str(text or '')
    return any(re.search(p,t) for p in SENSITIVE_PATTERNS)

def contains_real_send_action(text: str | None) -> bool:
    t=str(text or '')
    return any(re.search(p,t) for p in REAL_SEND_PATTERNS)

def sanitize_notification_text(text: Any) -> str:
    s=str(text or '')
    for p in SENSITIVE_PATTERNS: s=re.sub(p, '[REDACTED_SECRET]=', s)
    s=re.sub(r'sk-[A-Za-z0-9_-]{8,}', 'sk-***REDACTED***', s)
    s=re.sub(r'(?i)bearer\s+[a-z0-9._-]+', 'Bearer ***REDACTED***', s)
    return s

def mask_destination(value: Any) -> str:
    s=str(value or '').strip()
    if not s: return 'masked:empty'
    if s.startswith('mailto:'): s=s[7:]
    m=re.search(r'\[([^\]]+)\]\(mailto:([^\)]+)\)', s)
    if m: s=m.group(2)
    if s.startswith('wechat:'): return 'wechat:webhook:***masked***'
    if s.startswith('telegram:'): return 'telegram:***'+s[-2:]
    if s.startswith('http://') or s.startswith('https://'): return re.sub(r'//([^/]+).*', r'//\1/***masked***', s)
    if '@' in s:
        a,b=s.split('@',1); return (a[:2]+'***@'+b[:1]+'***')
    digits=re.sub(r'\D','',s)
    if len(digits)>=7: return s[:3]+'***'+s[-2:]
    return s[:2]+'***'

def validate_notification_is_dry_run(obj):
    return bool(getattr(obj,'dry_run', True)) and not bool(getattr(obj,'real_send_enabled',False)) and not bool(getattr(obj,'external_network_enabled',False))

def assert_no_real_send(obj):
    if bool(getattr(obj,'real_send_enabled',False)): raise ValueError('real_send_enabled is blocked')
    return True

def assert_no_external_network(obj):
    if bool(getattr(obj,'external_network_enabled',False)): raise ValueError('external_network_enabled is blocked')
    return True

def validate_delivery_plan_safety(plan):
    blocked=[]
    if not getattr(plan,'dry_run',True): blocked.append('dry_run must be true')
    if getattr(plan,'real_send_enabled',False): blocked.append('real_send_enabled is blocked')
    if getattr(plan,'external_network_enabled',False): blocked.append('external_network_enabled is blocked')
    msg=getattr(plan,'message',None)
    text=(getattr(msg,'subject','')+'\n'+getattr(msg,'body','')) if msg else ''
    if contains_sensitive_secret(text): blocked.append('message contains sensitive secret pattern')
    if contains_real_send_action(text): blocked.append('message contains real send action pattern')
    return {"passed": not blocked, "blocked_reasons": blocked, "safety_note": SAFETY_NOTE}

def validate_notification_report_safety(report):
    blocked=[]
    for p in getattr(report,'delivery_plans',[]): blocked += validate_delivery_plan_safety(p)['blocked_reasons']
    return {"passed": not blocked, "blocked_reasons": blocked, "safety_note": SAFETY_NOTE}
