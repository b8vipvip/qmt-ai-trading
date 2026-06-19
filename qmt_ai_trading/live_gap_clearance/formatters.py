from __future__ import annotations
import json
from .models import *
def _json(r): return json.dumps(to_plain(r),ensure_ascii=False,indent=2)
def format_live_gap_clearance_report_json(r): return _json(r)
def format_evidence_remediation_report_json(r): return _json(r)
def format_human_closure_recheck_report_json(r): return _json(r)
def format_next_readonly_check_report_json(r): return _json(r)
def _ev(report,cat): return [e for e in report.evidence if enum_value(e.category)==cat]
def _ev_lines(items): return [f'- {enum_value(e.status)} {e.path}: {e.summary}' for e in items] or ['- Not found / skipped.']
def format_live_gap_clearance_report_markdown(report:LiveGapClearanceReport)->str:
    lines=['# Stage54 Final Pre-gray Gap Clearance Plan','','## Decision',str(enum_value(report.decision)),'','## Safety Note',report.safety_note,'','## Evidence Summary',f"- total_evidence: {report.summary.get('total_evidence',len(report.evidence))}",f"- critical: {report.summary.get('critical',0)}",f"- warnings: {report.summary.get('warnings',len(report.warnings))}",'- read_only: True','- dry_run_only: True','- no_trade_authorization: True','- live_trading_enabled: False','- no_task_registered: True']
    for cat,title in [('STAGE50_FINAL_ARCHIVE','Stage50 Final Archive Evidence'),('STAGE51_ARCHIVE_LOCK','Stage51 Archive Lock Evidence'),('STAGE52_LOCK_CONSISTENCY','Stage52 Lock Consistency Evidence'),('STAGE53_ARCHIVE_VERIFICATION','Stage53 Archive Verification Evidence'),('ROADMAP_STAGE_PLAN','Roadmap Stage Plan Evidence'),('UI_PRODUCTIZATION_PLAN','UI Productization Plan Evidence')]: lines += ['',f'## {title}']+_ev_lines(_ev(report,cat))
    lines += ['','## Gap Clearance Plan']+[f'- {enum_value(i.status)} {i.title}: {i.summary} Required action: {i.required_action}' for i in report.gap_clearance]
    lines += ['','## Evidence Remediation Review']+[f'- {enum_value(i.status)} {i.title}: {i.summary}' for i in report.evidence_remediation]
    lines += ['','## Human Closure Recheck']+[f'- [ ] {i.role}: {i.statement}' for i in report.human_closure_recheck]
    lines += ['','## Next Read-only Check Plan']+[f'- {enum_value(i.status)} {i.title}: {i.summary}' for i in report.next_readonly_check_plan]
    lines += ['','## Required Manual Confirmations']+[f'- [ ] {x}' for x in report.required_manual_confirmations]
    lines += ['','## Blocking Reasons']+([f'- {x}' for x in report.blocking_reasons] or ['- None'])
    lines += ['','## Warnings']+([f'- {x}' for x in report.warnings] or ['- None'])
    lines += ['','## Next Stage Preview','Stage55 仍不得直接实盘；只能进入 QMT 实机 dry-run 环境最终校准，不调用 xttrader、不查询真实账户、不下单。','']
    return '\n'.join(lines)
def format_evidence_remediation_markdown(r): return '\n'.join(['# Stage54 Evidence Remediation Review','','## Decision',str(enum_value(r.decision)),'','## Safety Note',r.safety_note]+[f'\n## {i.title}\n- Status: {enum_value(i.status)}\n- {i.summary}\n- 灰度前缺口清零计划不等于实盘授权。' for i in r.items])+'\n'
def format_human_closure_recheck_markdown(r): return '\n'.join(['# Stage54 Human Closure Recheck','','## Decision',str(enum_value(r.decision)),'','## Safety Note',r.safety_note]+[f'\n## {i.role}\n- [ ] {i.statement}\n- 不代表实盘授权。\n- 未来真实执行仍需单独审批。' for i in r.items])+'\n'
def format_next_readonly_check_markdown(r): return '\n'.join(['# Stage54 Next Read-only Check Plan','','## Decision',str(enum_value(r.decision)),'','## Safety Note',r.safety_note]+[f'\n## {i.title}\n- {i.summary}\n- 不代表实盘授权。' for i in r.items])+'\n'
