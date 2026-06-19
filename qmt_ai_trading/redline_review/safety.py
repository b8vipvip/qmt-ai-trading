from __future__ import annotations
from pathlib import Path
from typing import Any
from uuid import uuid4
from .models import RedlineCategory, RedlineFinding, RedlineReviewConfig, RedlineReviewReport, RedlineSeverity, RedlineStatus, SAFETY_NOTE

SENSITIVE_KEYS=("token","key","password","secret","account","credential")
def sanitize_redline_metadata(metadata: dict[str, Any] | None)->dict[str,Any]:
    clean={}
    for k,v in dict(metadata or {}).items():
        if any(s in str(k).lower() for s in SENSITIVE_KEYS): clean[str(k)]="***REDACTED***"
        elif isinstance(v, dict): clean[str(k)]=sanitize_redline_metadata(v)
        else: clean[str(k)]=v
    return clean

def build_default_redline_review_config(repo_root: str | Path='.', include_paths=None, exclude_paths=None, operator_name='', reviewer_name='', metadata=None)->RedlineReviewConfig:
    cfg=RedlineReviewConfig(repo_root=str(repo_root), operator_name=operator_name, reviewer_name=reviewer_name)
    if include_paths is not None: cfg.include_paths=[str(x) for x in include_paths]
    if exclude_paths is not None: cfg.exclude_paths=[str(x) for x in exclude_paths]
    cfg.allowed_live_markers=default_allowed_context_markers(); cfg.allowed_dry_run_markers=default_allowed_context_markers()
    cfg.metadata.update(sanitize_redline_metadata(metadata)); return cfg

def default_forbidden_markers()->list[str]:
    return ['--live-enabled','--execute-live','--real-send','live_enabled=True','execute_live=True','real_order_enabled=True','real_send=True','xttrader','place_order','submit_order','order_stock','query_stock_asset','query_stock_positions','query_stock_orders','query_stock_trades','查询资金','查询持仓','查询订单','查询成交','requests.post','smtp','sendMessage','webhook','自动批准','自动approve','绕过风控','bypass Risk Gate','bypass Human Approval','auto live','auto approve','auto submit']

def default_allowed_context_markers()->list[str]:
    return ['禁止','不允许','does not','no real','dry-run only','review-only','preparation-only','read-only','不启用','不调用','不查询','不下单','不真实发送','dry-run','只读']

def _cat(marker:str)->RedlineCategory:
    m=marker.lower()
    if 'execute' in m or m=='--execute': return RedlineCategory.EXECUTE_SWITCH
    if 'live' in m or 'real_order' in m: return RedlineCategory.LIVE_SWITCH
    if 'xttrader' in m: return RedlineCategory.XTTRADER
    if 'query_stock' in m or marker in {'查询资金','查询持仓','查询订单','查询成交'}: return RedlineCategory.ACCOUNT_QUERY
    if any(x in m for x in ['place_order','submit_order','order_stock']): return RedlineCategory.ORDER_SUBMISSION
    if any(x in m for x in ['requests.post','smtp','sendmessage','webhook','real-send','real_send']): return RedlineCategory.REAL_NOTIFICATION
    if 'risk' in m or '风控' in m: return RedlineCategory.RISK_BYPASS
    if 'approval' in m or 'approve' in m or '批准' in m: return RedlineCategory.APPROVAL_BYPASS
    return RedlineCategory.SYSTEM

def classify_marker(marker: str, path: str | Path, line_text: str)->RedlineFinding:
    p=str(path); text=line_text or ''; low=text.lower(); pl=p.lower()
    allowed= any(x.lower() in low for x in default_allowed_context_markers()) or '/tests/' in ('/'+pl) or pl.startswith('tests/') or '/docs/' in ('/'+pl) or pl.startswith('docs/')
    cat=_cat(marker)
    status=RedlineStatus.WARN if allowed else RedlineStatus.FAIL
    sev=RedlineSeverity.WARN if allowed else RedlineSeverity.CRITICAL
    if pl.startswith('docs/'): cat=RedlineCategory.DOCUMENTATION
    return RedlineFinding(finding_id=f"redline-{uuid4().hex[:8]}", category=cat, status=status, severity=sev, path=p, marker=marker, message=f"Detected red-line marker '{marker}' in {'allowed explanatory' if allowed else 'execution-risk'} context.", remediation="Keep as documented review-only evidence or remove/disable the dangerous entry point before any future stage.", metadata={"line_text_preview": text[:240]})

def validate_redline_review_report_safety(report: RedlineReviewReport)->None:
    if report.safety_note != SAFETY_NOTE: raise ValueError('missing required red-line safety note')
    report.metadata = sanitize_redline_metadata(report.metadata)
