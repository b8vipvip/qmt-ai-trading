from __future__ import annotations
import json
from .models import LiveGrayCheck, LiveGrayReadinessReport
from .checklist import format_gray_manual_review_checklist

def format_live_gray_check(check: LiveGrayCheck) -> str:
    return f"- [{getattr(check.status,'value',check.status)}] {getattr(check.scope,'value',check.scope)} / {check.title}: {check.message}"
def format_live_gray_report_json(report: LiveGrayReadinessReport) -> str:
    return json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
def format_live_gray_report_markdown(report: LiveGrayReadinessReport) -> str:
    d=report.to_dict(); cfg=d["config"]
    failed=[c for c in report.checks if str(getattr(c.status,'value',c.status))=='FAIL']
    lines=["# Live Gray Readiness Report", "", "## Decision", f"- Decision: {d['decision']}", f"- Success: {report.success}", f"- Message: {report.message}", "", "## Summary"]
    for k,v in (report.summary or {}).items(): lines.append(f"- {k}: {v}")
    lines += ["", "## Live/Gray switches", f"- live_enabled: {cfg['live_enabled']}", f"- gray_enabled: {cfg['gray_enabled']}", "", "## Capital limits", f"- max_total_capital: {cfg['max_total_capital']}", f"- max_single_order_value: {cfg['max_single_order_value']}", f"- max_symbol_weight: {cfg['max_symbol_weight']}", f"- max_portfolio_weight: {cfg['max_portfolio_weight']}", "", "## Symbol whitelist", f"- allowed_symbols: {', '.join(cfg['allowed_symbols']) if cfg['allowed_symbols'] else '(empty)'}", "", "## Required evidence"]
    for c in report.checks: lines.append(format_live_gray_check(c))
    lines += ["", "## Failed checks"]
    lines += [format_live_gray_check(c) for c in failed] or ["- None"]
    lines += ["", "## Manual review checklist", format_gray_manual_review_checklist(report), "", "## Blocked reasons"]
    lines += [f"- {x}" for x in report.blocked_reasons] or ["- None"]
    lines += ["", "## Safety note", report.safety_note]
    return "\n".join(lines)
