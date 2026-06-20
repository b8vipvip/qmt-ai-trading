from __future__ import annotations
import json
from pathlib import Path
from .models import *
SENSITIVE=['.env','token','key','secret','credential']
def _blocked(path):
    s=str(path).replace('\\','/').lower(); name=Path(path).name.lower()
    return any(x in name for x in SENSITIVE) or '/market_data/' in s or '/logs/' in s or (('/reports/' in s) and 'validation_logs' not in s) or s.endswith(('.db','.sqlite','.duckdb'))
def read_console_json(path):
    p=Path(path)
    if _blocked(p): return LocalConsoleEvidence(LocalConsoleCategory.SENSITIVE_FILE,LocalConsoleStatus.FAIL,LocalConsoleSeverity.CRITICAL,p.name,'sensitive or runtime path blocked',str(p))
    if not p.exists(): return LocalConsoleEvidence(LocalConsoleCategory.REPORT_DETAIL,LocalConsoleStatus.UNAVAILABLE,LocalConsoleSeverity.WARN,p.name,'missing report',str(p))
    try:
        data=json.loads(p.read_text(encoding='utf-8'))
        return LocalConsoleEvidence(LocalConsoleCategory.REPORT_DETAIL,LocalConsoleStatus.PASS,LocalConsoleSeverity.INFO,p.name,'json report readable',str(p),{'data':data})
    except Exception as e:
        return LocalConsoleEvidence(LocalConsoleCategory.REPORT_DETAIL,LocalConsoleStatus.WARN,LocalConsoleSeverity.WARN,p.name,f'json read warning: {e}',str(p))
def read_console_markdown_summary(path, max_chars=1200):
    p=Path(path)
    if _blocked(p): return 'BLOCKED: sensitive or runtime path'
    if not p.exists(): return 'UNAVAILABLE: missing markdown'
    return p.read_text(encoding='utf-8',errors='replace')[:max_chars]
def read_latest_validation_summary(log_dir):
    d=Path(log_dir)
    if not d.exists(): return LocalConsoleEvidence(LocalConsoleCategory.VALIDATION_LOG,LocalConsoleStatus.UNAVAILABLE,LocalConsoleSeverity.WARN,'latest validation','validation_logs unavailable',str(d))
    files=sorted(d.glob('stage*_validation_*.log'), key=lambda p:p.stat().st_mtime, reverse=True)[:1]
    if not files: return LocalConsoleEvidence(LocalConsoleCategory.VALIDATION_LOG,LocalConsoleStatus.UNAVAILABLE,LocalConsoleSeverity.WARN,'latest validation','no validation log found',str(d))
    txt=files[0].read_text(encoding='utf-8',errors='replace')[-2000:]
    return LocalConsoleEvidence(LocalConsoleCategory.VALIDATION_LOG,LocalConsoleStatus.PASS,LocalConsoleSeverity.INFO,'latest validation',txt,str(files[0]),{'latest_only':True})
def build_report_detail_from_json(stage,title,path):
    ev=read_console_json(path); data=ev.metadata.get('data') or {}; summary=data.get('summary') or {}
    return LocalConsoleReportDetail(stage,title,str(path),ev.status,ev.summary,data.get('decision',''),int(summary.get('critical_count',data.get('critical_count',0)) or 0),data.get('warnings',[]))
def build_report_detail_from_markdown(stage,title,path):
    return LocalConsoleReportDetail(stage,title,str(path),LocalConsoleStatus.PASS if Path(path).exists() else LocalConsoleStatus.UNAVAILABLE,read_console_markdown_summary(path))
def safe_read_report(path): return read_console_json(path)
