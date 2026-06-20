from __future__ import annotations
import json
from pathlib import Path
from .detail_models import *
SENSITIVE=['.env','token','key','secret','credential']
def _blocked(path):
    s=str(path).replace('\\','/').lower(); n=Path(path).name.lower()
    return any(x in n for x in SENSITIVE) or '/market_data/' in s or s.endswith(('.db','.sqlite','.duckdb'))
def clean_nul_text(text: str)->str: return text.replace('\x00','')
def _decode_bytes(data: bytes):
    for enc in ('utf-8-sig','utf-8','utf-16-le','utf-16-be'):
        try:
            txt=data.decode(enc)
            if txt.count('\x00') > max(8, len(txt)//20) and enc.startswith('utf-8'):
                continue
            return clean_nul_text(txt), enc
        except UnicodeError: pass
    return clean_nul_text(data.decode('utf-8',errors='replace')), 'utf-8-replace'
def decode_text_file_auto(path, max_bytes: int|None=None):
    p=Path(path); data=p.read_bytes() if max_bytes is None else p.read_bytes()[:max_bytes]
    txt, enc=_decode_bytes(data)
    if '\x00' in txt:
        raw=p.read_bytes() if max_bytes is None else p.read_bytes()[:max_bytes]
        for enc2 in ('utf-16-le','utf-16-be'):
            try:
                cand=clean_nul_text(raw.decode(enc2))
                if cand.count('\x00') < txt.count('\x00'): return cand, enc2
            except UnicodeError: pass
    return clean_nul_text(txt), enc
def _summary_from_data(data):
    if isinstance(data, dict):
        return str(data.get('summary') or data.get('decision') or data.get('status') or 'json report readable')
    return 'json report readable'
def read_console_detail_json(path):
    p=Path(path)
    if _blocked(p): return LocalConsoleDetailEvidence(path=str(p),status=LocalConsoleDetailStatus.FAIL,severity=LocalConsoleDetailSeverity.CRITICAL,summary='BLOCKED sensitive/runtime path')
    if not p.exists(): return LocalConsoleDetailEvidence(path=str(p),status=LocalConsoleDetailStatus.UNAVAILABLE,severity=LocalConsoleDetailSeverity.WARN,summary='UNAVAILABLE missing json report')
    try:
        txt,_=decode_text_file_auto(p, max_bytes=512000); data=json.loads(txt)
        summary=data.get('summary') if isinstance(data,dict) else {}
        crit=int((summary or {}).get('critical_count', data.get('critical_count',0) if isinstance(data,dict) else 0) or 0)
        return LocalConsoleDetailEvidence(path=str(p),status=LocalConsoleDetailStatus.PASS,severity=LocalConsoleDetailSeverity.INFO,summary=_summary_from_data(data),decision=str(data.get('decision','') if isinstance(data,dict) else ''),critical_count=crit,warnings=list(data.get('warnings',[]) if isinstance(data,dict) else []),blocking_reasons=list(data.get('blocking_reasons',[]) if isinstance(data,dict) else []),metadata={'data':data})
    except Exception as e:
        return LocalConsoleDetailEvidence(path=str(p),status=LocalConsoleDetailStatus.WARN,severity=LocalConsoleDetailSeverity.WARN,summary=f'WARN json read failed: {e}')
def read_console_detail_markdown_summary(path, max_chars=1600):
    p=Path(path)
    if _blocked(p): return 'WARN BLOCKED sensitive/runtime path'
    if not p.exists(): return 'UNAVAILABLE missing markdown'
    try:
        txt,_=decode_text_file_auto(p, max_bytes=max_chars*8); return clean_nul_text(txt[:max_chars])
    except Exception as e: return f'WARN markdown read failed: {e}'
def read_latest_validation_detail(log_dir):
    d=Path(log_dir)
    if not d.exists(): return ConsoleValidationLogDetail(path=str(d),status=LocalConsoleDetailStatus.UNAVAILABLE,summary='UNAVAILABLE validation_logs missing')
    files=sorted(d.glob('stage*_validation_*.log'), key=lambda p:(p.stat().st_mtime, p.name), reverse=True)[:1]
    if not files: return ConsoleValidationLogDetail(path=str(d),status=LocalConsoleDetailStatus.UNAVAILABLE,summary='UNAVAILABLE no validation log found')
    p=files[0]
    try:
        size=p.stat().st_size; raw=p.read_bytes(); sample=raw[:6000]+(b'\n...TRUNCATED...\n'+raw[-6000:] if size>12000 else b'')
        txt,enc=_decode_bytes(sample); txt=clean_nul_text(txt)
        return ConsoleValidationLogDetail(path=str(p),status=LocalConsoleDetailStatus.PASS,severity=LocalConsoleDetailSeverity.INFO,encoding=enc,head=txt[:3000],tail=txt[-3000:],summary=txt[:1200])
    except Exception as e: return ConsoleValidationLogDetail(path=str(p),status=LocalConsoleDetailStatus.WARN,summary=f'WARN validation read failed: {e}',warnings=[str(e)])
def build_stage_detail_from_json(stage,path):
    ev=read_console_detail_json(path); ev.stage=stage; ev.title=stage; return ConsoleStageDetail(**ev.__dict__)
def build_stage_detail_from_markdown(stage,path):
    return ConsoleStageDetail(stage=stage,title=stage,path=str(path),status=LocalConsoleDetailStatus.PASS if Path(path).exists() else LocalConsoleDetailStatus.UNAVAILABLE,summary=read_console_detail_markdown_summary(path))
def safe_read_detail_report(path): return read_console_detail_json(path)
