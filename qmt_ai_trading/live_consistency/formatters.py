from __future__ import annotations
import json
from .models import *
def _json(r): return json.dumps(to_plain(r),ensure_ascii=False,indent=2)
def format_live_consistency_report_json(r): return _json(r)
def format_material_consistency_report_json(r): return _json(r)
def format_human_recheck_report_json(r): return _json(r)
def format_next_gray_check_report_json(r): return _json(r)
def _ev(report,cat): return [e for e in report.evidence if enum_value(e.category)==cat]
def _ev_lines(items): return [f"- {enum_value(e.status)} {e.path}: {e.summary}" for e in items] or ["- Not found / skipped."]
def format_live_consistency_report_markdown(report:LiveConsistencyReport)->str:
    lines=["# Stage49 Remediation Read-only Review and Material Consistency Check","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"","## Evidence Summary",f"- total_evidence: {report.summary.get('total_evidence',len(report.evidence))}",f"- critical: {report.summary.get('critical',0)}",f"- warnings: {report.summary.get('warnings',len(report.warnings))}","- read_only: True","- dry_run_only: True","- no_trade_authorization: True","- live_trading_enabled: False","- no_task_registered: True"]
    for cat,title in [("STAGE45_RUNBOOK","Stage45 Runbook Evidence"),("STAGE46_SIGNOFF","Stage46 Signoff Evidence"),("STAGE47_FINAL_REVIEW","Stage47 Final Review Evidence"),("STAGE48_ARCHIVE","Stage48 Archive Evidence")]: lines += ["",f"## {title}"]+_ev_lines(_ev(report,cat))
    lines += ["","## Remediation Read-only Review"]+[f"- {enum_value(i.status)} {i.title}: {i.summary} Required action: {i.required_action}" for i in report.remediation_review]
    lines += ["","## Material Consistency Check"]+[f"- {enum_value(i.status)} {i.title}: {i.summary}" for i in report.material_consistency]
    lines += ["","## Human Recheck Summary"]+[f"- [ ] {i.role}: {i.statement}" for i in report.human_recheck]
    lines += ["","## Next Gray Check Plan"]+[f"- {enum_value(i.status)} {i.title}: {i.summary}" for i in report.next_gray_check_plan]
    lines += ["","## Required Manual Confirmations"]+[f"- [ ] {x}" for x in report.required_manual_confirmations]
    lines += ["","## Blocking Reasons"]+([f"- {x}" for x in report.blocking_reasons] or ["- None"])
    lines += ["","## Warnings"]+([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["","## Next Stage Preview","Stage50 仍不得直接实盘；只能继续做最终归档复核、材料一致性封版、人工核验闭环或更严格的灰度前检查。",""]
    return "\n".join(lines)
def format_material_consistency_markdown(r): return "\n".join(["# Stage49 Material Consistency Check","","## Decision",str(enum_value(r.decision)),"","## Safety Note",r.safety_note]+[f"\n## {i.title}\n- Status: {enum_value(i.status)}\n- {i.summary}" for i in r.items])+"\n"
def format_human_recheck_markdown(r): return "\n".join(["# Stage49 Human Recheck","","## Decision",str(enum_value(r.decision)),"","## Safety Note",r.safety_note]+[f"\n## {i.role}\n- [ ] {i.statement}\n- 不代表实盘授权。\n- 未来真实执行仍需单独审批。" for i in r.items])+"\n"
def format_next_gray_check_markdown(r): return "\n".join(["# Stage49 Next Gray Check Plan","","## Decision",str(enum_value(r.decision)),"","## Safety Note",r.safety_note]+[f"\n## {i.title}\n- {i.summary}" for i in r.items])+"\n"
