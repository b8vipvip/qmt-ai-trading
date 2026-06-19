from __future__ import annotations
from pathlib import Path
import json
from .formatters import format_redline_review_report_json, format_redline_review_report_markdown
from .models import RedlineReviewReport
from .safety import build_default_redline_review_config, validate_redline_review_report_safety
from .scanner import aggregate_redline_findings, iter_scan_files, scan_file_for_redline_markers, scan_scheduler_preview_text, scan_dashboard_for_order_entry, scan_sensitive_files

def run_redline_review(*, config=None, repo_root=None, scheduler_preview_text=None, dashboard_path_or_text=None, metadata=None):
    cfg=config or build_default_redline_review_config(repo_root or '.')
    if repo_root is not None: cfg.repo_root=str(repo_root)
    findings=[]
    for p in iter_scan_files(cfg.repo_root, cfg.include_paths, cfg.exclude_paths): findings.extend(scan_file_for_redline_markers(p,cfg))
    if scheduler_preview_text: findings.extend(scan_scheduler_preview_text(scheduler_preview_text,cfg))
    if dashboard_path_or_text: findings.extend(scan_dashboard_for_order_entry(dashboard_path_or_text,cfg))
    findings.extend(scan_sensitive_files(cfg.repo_root,cfg))
    agg=aggregate_redline_findings(findings,cfg)
    report=RedlineReviewReport(decision=agg['decision'], config=cfg, findings=findings, blocked_reasons=agg['blocked_reasons'], warnings=agg['warnings'], metadata={"aggregate":agg['summary'], **(metadata or {})})
    report.success=True; report.message='Generated review-only red-line review report; this is not trading authorization.'
    validate_redline_review_report_safety(report); return report

def run_redline_review_from_repo(repo_root='.', **kwargs): return run_redline_review(repo_root=repo_root, **kwargs)
def save_redline_review_report(report, output_path):
    p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
    text=format_redline_review_report_json(report) if p.suffix.lower()=='.json' else format_redline_review_report_markdown(report)
    p.write_text(text, encoding='utf-8'); return p
def load_redline_review_report(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    from .models import RedlineReviewConfig, RedlineFinding
    cfg=RedlineReviewConfig(**data.get('config',{})); fs=[RedlineFinding(**x) for x in data.get('findings',[])]
    return RedlineReviewReport(report_id=data.get('report_id',''), created_at=data.get('created_at',''), decision=data.get('decision','NEED_MORE_EVIDENCE'), config=cfg, findings=fs, blocked_reasons=data.get('blocked_reasons',[]), warnings=data.get('warnings',[]), summary=data.get('summary',''), safety_note=data.get('safety_note',''), success=data.get('success',True), message=data.get('message',''), metadata=data.get('metadata',{}))
