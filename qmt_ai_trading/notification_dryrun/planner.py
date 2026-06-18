from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable
from .formatters import format_delivery_plan
from .models import NotificationChannel, NotificationDeliveryPlan, NotificationRecipient, NotificationSendMode
from .safety import mask_destination, validate_delivery_plan_safety
REAL={NotificationChannel.EMAIL.value,NotificationChannel.TELEGRAM.value,NotificationChannel.WECHAT.value}

def _ch(x): return x if isinstance(x, NotificationChannel) else NotificationChannel[str(x).upper()]

def build_recipients_from_config(recipients=None, channels=None):
    chans=[_ch(c) for c in (channels or [NotificationChannel.FILE, NotificationChannel.CONSOLE])]
    raw=[]
    if isinstance(recipients,str): raw=[x.strip() for x in recipients.split(',') if x.strip()]
    elif recipients: raw=list(recipients)
    out=[]
    for ch in chans:
        vals=raw or [ch.value.lower()]
        for v in vals:
            out.append(NotificationRecipient(channel=ch, display_name=f"{ch.value} dry-run recipient", destination_masked=mask_destination(v), metadata={"masked": True}))
    return out

def build_delivery_plan(message, recipient, send_mode='DRY_RUN'):
    ch=_ch(recipient.channel)
    mode=NotificationSendMode.SUPPRESSED if ch.value in REAL else NotificationSendMode[str(send_mode).upper()]
    plan=NotificationDeliveryPlan(send_mode=mode, channel=ch, recipient=recipient, message=message, dry_run=True, real_send_enabled=False, external_network_enabled=False)
    if ch.value in REAL: plan.blocked_reasons.append(f"{ch.value} real delivery suppressed in stage34 dry-run")
    plan.blocked_reasons += validate_delivery_plan_safety(plan)['blocked_reasons']
    return plan

def build_delivery_plans(messages, recipients, send_mode='DRY_RUN'):
    return [build_delivery_plan(m,r,send_mode) for m in messages for r in recipients]

def suppress_real_channels(plans):
    for p in plans:
        if str(getattr(p.channel,'value',p.channel)) in REAL:
            p.send_mode=NotificationSendMode.SUPPRESSED; p.real_send_enabled=False; p.external_network_enabled=False
            if not p.blocked_reasons: p.blocked_reasons.append('real channel suppressed')
    return plans

def save_delivery_plan_preview(plans, output_dir):
    root=Path(output_dir); root.mkdir(parents=True, exist_ok=True); files=[]
    for p in plans:
        base=root/f"{p.plan_id}.notification_preview"
        (base.with_suffix('.md')).write_text(format_delivery_plan(p),encoding='utf-8')
        (base.with_suffix('.json')).write_text(json.dumps(p.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8')
        files += [str(base.with_suffix('.md')), str(base.with_suffix('.json'))]
    return files
