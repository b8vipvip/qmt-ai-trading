from __future__ import annotations
import json
from .models import *
def _json(r): return json.dumps(to_plain(r),ensure_ascii=False,indent=2)
def format_live_final_archive_report_json(r): return _json(r)
def format_material_seal_report_json(r): return _json(r)
def format_human_closure_report_json(r): return _json(r)
def format_next_readonly_check_report_json(r): return _json(r)
def _ev(report,cat): return [e for e in report.evidence if enum_value(e.category)==cat]
def _ev_lines(items): return [f"- {enum_value(e.status)} {e.path}: {e.summary}" for e in items] or ["- Not found / skipped."]
def format_live_final_archive_report_markdown(report:LiveFinalArchiveReport)->str:
    lines=["# Stage50 Final Archive Review and Material Consistency Seal","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"READY_FOR_FINAL_ARCHIVE_REVIEW 只表示最终归档复核与材料一致性封版材料可供人工复核，不是实盘授权。","","## Evidence Summary",f"- total_evidence: {report.summary.get('total_evidence',len(report.evidence))}",f"- critical: {report.summary.get('critical',0)}",f"- warnings: {report.summary.get('warnings',len(report.warnings))}","- read_only: True","- dry_run_only: True","- no_trade_authorization: True","- live_trading_enabled: False","- no_task_registered: True"]
    for cat,title in [("STAGE49_CONSISTENCY","Stage49 Consistency Evidence"),("STAGE46_SIGNOFF","Stage46 Signoff Evidence"),("STAGE47_FINAL_REVIEW","Stage47 Final Review Evidence"),("STAGE48_ARCHIVE","Stage48 Archive Evidence")]: lines += ["",f"## {title}"]+_ev_lines(_ev(report,cat))
    lines += ["","## Final Archive Review"]+[f"- {enum_value(i.status)} {i.title}: {i.summary} Required action: {i.required_action}" for i in report.final_archive_review]
    lines += ["","## Material Consistency Seal"]+[f"- {enum_value(i.status)} {i.title}: {i.summary}" for i in report.material_seal]
    lines += ["","## Human Verification Closure"]+[f"- [ ] {i.role}: {i.statement}" for i in report.human_closure]
    lines += ["","## Next Read-only Check Plan"]+[f"- {enum_value(i.status)} {i.title}: {i.summary}" for i in report.next_readonly_check_plan]
    lines += ["","## Required Manual Confirmations"]+[f"- [ ] {x}" for x in report.required_manual_confirmations]
    lines += ["","## Blocking Reasons"]+([f"- {x}" for x in report.blocking_reasons] or ["- None"])
    lines += ["","## Warnings"]+([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["","## Next Stage Preview","Stage51 仍不得直接实盘；只能继续做最终只读封版复核、材料归档锁定、人工核验闭环复查或更严格的灰度前检查。",""]
    return "\n".join(lines)
def format_material_seal_markdown(r): return "\n".join(["# Stage50 Material Consistency Seal","","## Decision",str(enum_value(r.decision)),"","## Safety Note",r.safety_note]+[f"\n## {i.title}\n- Status: {enum_value(i.status)}\n- {i.summary}" for i in r.items])+"\n"
def format_human_closure_markdown(r): return "\n".join(["# Stage50 Human Verification Closure","","## Decision",str(enum_value(r.decision)),"","## Safety Note",r.safety_note]+[f"\n## {i.role}\n- [ ] {i.statement}\n- 不代表实盘授权。\n- 未来真实执行仍需单独审批。" for i in r.items])+"\n"
def format_next_readonly_check_markdown(r): return "\n".join(["# Stage50 Next Read-only Check Plan","","## Decision",str(enum_value(r.decision)),"","## Safety Note",r.safety_note]+[f"\n## {i.title}\n- {i.summary}" for i in r.items])+"\n"
