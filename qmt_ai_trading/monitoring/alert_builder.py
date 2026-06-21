from __future__ import annotations
import hashlib
from .models import MonitoringAlert
def make_alert(rule_id,severity,source_stage,source_file,message,evidence,recommendation,created_at):
    seed=f'{rule_id}|{source_stage}|{source_file}|{message}|{evidence}'
    aid='ALERT-'+hashlib.sha256(seed.encode()).hexdigest()[:12].upper()
    return MonitoringAlert(aid,rule_id,severity,source_stage,source_file,message,evidence,recommendation,True,True,True,True,created_at).to_dict()
