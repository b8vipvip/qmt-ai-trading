from __future__ import annotations
from pathlib import Path
from uuid import uuid4
from .models import RedlineCategory, RedlineFinding, RedlineReviewConfig, RedlineReviewDecision, RedlineSeverity, RedlineStatus
from .safety import classify_marker, default_forbidden_markers
MAX_BYTES=1_000_000

def _excluded(path:Path, root:Path, excludes:list[str])->bool:
    rel=path.relative_to(root).as_posix() if path.is_absolute() and root in path.parents or path==root else path.as_posix()
    return any(ex.strip('/').replace('**','') in rel for ex in excludes)
def iter_scan_files(repo_root, include_paths, exclude_paths):
    root=Path(repo_root).resolve()
    for inc in include_paths:
        base=(root/inc).resolve()
        if not base.exists(): continue
        for p in ([base] if base.is_file() else base.rglob('*')):
            if p.is_file() and not _excluded(p, root, exclude_paths): yield p

def scan_text_for_redline_markers(text, path, config):
    out=[]
    for i,line in enumerate(str(text).splitlines(),1):
        for marker in default_forbidden_markers()+['--execute']:
            if marker.lower() in line.lower():
                f=classify_marker(marker,path,line); f.line_number=i; out.append(f)
    return out

def scan_file_for_redline_markers(path, config):
    p=Path(path)
    if not p.exists():
        return [RedlineFinding(f"redline-{uuid4().hex[:8]}", RedlineCategory.SYSTEM, RedlineStatus.SKIPPED, RedlineSeverity.WARN, str(p), None, '', 'File not found; skipped.', 'Confirm path if required.')]
    try:
        if p.stat().st_size>MAX_BYTES:
            return [RedlineFinding(f"redline-{uuid4().hex[:8]}", RedlineCategory.RUNTIME_ARTIFACT, RedlineStatus.WARN, RedlineSeverity.WARN, str(p), None, '', 'Large file skipped.', 'Review manually if needed.')]
        return scan_text_for_redline_markers(p.read_text(encoding='utf-8', errors='replace'), p, config)
    except OSError as exc:
        return [RedlineFinding(f"redline-{uuid4().hex[:8]}", RedlineCategory.SYSTEM, RedlineStatus.WARN, RedlineSeverity.WARN, str(p), None, '', f'Read failed: {exc}', 'Review local permissions.')]

def scan_scheduler_preview_text(text, config):
    fs=scan_text_for_redline_markers(text,'scheduler-preview',config)
    for f in fs:
        if f.marker in {'--execute','--execute-live'}: f.category=RedlineCategory.SCHEDULER; f.status=RedlineStatus.FAIL; f.severity=RedlineSeverity.CRITICAL
    return fs

def scan_dashboard_for_order_entry(path_or_text, config):
    s=str(path_or_text)
    text=Path(s).read_text(encoding='utf-8', errors='replace') if Path(s).exists() and Path(s).is_file() else s
    fs=[]
    for marker in ['submit order','order button','execute live','下单按钮']:
        if marker.lower() in text.lower():
            fs.append(RedlineFinding(f"redline-{uuid4().hex[:8]}", RedlineCategory.DASHBOARD, RedlineStatus.FAIL, RedlineSeverity.CRITICAL, s[:120], None, marker, 'Dashboard order-entry marker detected.', 'Remove all order-entry controls.'))
    return fs+scan_text_for_redline_markers(text,'dashboard',config)

def scan_sensitive_files(repo_root, config):
    root=Path(repo_root); out=[]
    for name in ['.env','.env.local','.env.production']:
        p=root/name
        if p.exists(): out.append(RedlineFinding(f"redline-{uuid4().hex[:8]}", RedlineCategory.SENSITIVE_FILE, RedlineStatus.FAIL, RedlineSeverity.CRITICAL, str(p), None, name, 'Sensitive env file exists; content not read.', 'Keep out of repo and review locally.'))
    return out

def aggregate_redline_findings(findings, config):
    findings=list(findings); crit=[f for f in findings if str(f.status).endswith('FAIL') or str(f.severity).endswith('CRITICAL')]
    warn=[f for f in findings if str(f.status).endswith('WARN')]
    decision=RedlineReviewDecision.BLOCKED if crit else (RedlineReviewDecision.NEED_MORE_EVIDENCE if warn else RedlineReviewDecision.READY_FOR_REDLINE_REVIEW)
    return {"decision":decision,"blocked_reasons":[f"{f.path}:{f.line_number or ''} {f.marker} {f.message}" for f in crit],"warnings":[f"{f.path}:{f.line_number or ''} {f.marker} {f.message}" for f in warn],"summary":{"total_findings":len(findings),"critical":len(crit),"warnings":len(warn),"ready_for_redline_review_not_trade_authorization":True}}
