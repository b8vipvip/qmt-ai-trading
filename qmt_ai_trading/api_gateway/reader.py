from __future__ import annotations
import json
from pathlib import Path
from .models import ApiGatewayReadResult, ApiGatewayStatus
SENSITIVE=('env','token','key','secret','credential')
def safe_relative_path(repo_root, path):
    root=Path(repo_root).resolve(); p=(root / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if root not in p.parents and p != root: raise ValueError('path outside repo root')
    if any(s in p.name.lower() for s in SENSITIVE): raise ValueError('sensitive file blocked')
    return p
def summarize_markdown(text: str, max_chars: int=2000): return text[:max_chars] + ('\n...[truncated]' if len(text)>max_chars else '')
def read_markdown_report(path, max_chars=4000):
    try:
        p=Path(path)
        if not p.exists(): return ApiGatewayReadResult(ok=False,path=str(p),status=ApiGatewayStatus.UNAVAILABLE,blocking_reasons=['file unavailable'])
        return ApiGatewayReadResult(ok=True,path=str(p),status=ApiGatewayStatus.PASS,summary=p.name,data={'summary':summarize_markdown(p.read_text(encoding='utf-8',errors='ignore'),max_chars)})
    except Exception as e: return ApiGatewayReadResult(ok=False,path=str(path),status=ApiGatewayStatus.WARN,warnings=[str(e)])
def read_json_report(path):
    try:
        p=Path(path)
        if not p.exists(): return ApiGatewayReadResult(ok=False,path=str(p),status=ApiGatewayStatus.UNAVAILABLE,blocking_reasons=['file unavailable'])
        return ApiGatewayReadResult(ok=True,path=str(p),status=ApiGatewayStatus.PASS,summary=p.name,data=json.loads(p.read_text(encoding='utf-8')))
    except Exception as e: return ApiGatewayReadResult(ok=False,path=str(path),status=ApiGatewayStatus.WARN,warnings=[str(e)])
def read_latest_validation_log(log_dir, pattern='stage*_validation_*.log', max_chars=4000):
    try:
        files=sorted(Path(log_dir).glob(pattern), key=lambda p:p.stat().st_mtime, reverse=True)
        if not files: return ApiGatewayReadResult(ok=False,path=str(log_dir),status=ApiGatewayStatus.UNAVAILABLE,blocking_reasons=['latest validation log unavailable'])
        p=files[0]; txt=p.read_text(encoding='utf-8',errors='ignore')
        return ApiGatewayReadResult(ok=True,path=str(p),status=ApiGatewayStatus.PASS,summary=p.name,data={'tail':txt[-max_chars:]})
    except Exception as e: return ApiGatewayReadResult(ok=False,path=str(log_dir),status=ApiGatewayStatus.WARN,warnings=[str(e)])
