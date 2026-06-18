from __future__ import annotations
import json
from .models import GrayRehearsalReport

def format_gray_rehearsal_step(step):
    return f"- **{step.title}** [{getattr(step.status,'value',step.status)}]: {step.message}"
def format_gray_rehearsal_scenario(result):
    lines=[f"### {result.title}",f"Decision: {getattr(result.decision,'value',result.decision)}",result.summary]
    lines += [format_gray_rehearsal_step(s) for s in result.steps]
    if result.blocked_reasons: lines += ["Blocked reasons:", *[f"- {x}" for x in result.blocked_reasons]]
    if result.warnings: lines += ["Warnings:", *[f"- {x}" for x in result.warnings]]
    return "\n".join(lines)
def format_gray_rehearsal_report_markdown(report: GrayRehearsalReport):
    lines=["# Gray Rehearsal Report","","## Gray rehearsal summary",report.summary or report.message,"",f"## Decision\n{getattr(report.decision,'value',report.decision)}","","## Scenarios"]
    lines += [format_gray_rehearsal_scenario(s) for s in report.scenarios]
    blocked=[b for s in report.scenarios for b in s.blocked_reasons]; warnings=[w for s in report.scenarios for w in s.warnings]
    lines += ["","## Checklist", *[f"- [ ] {x}" for x in report.checklist],"","## Blocked reasons", *([f"- {x}" for x in blocked] or ["- None"]),"","## Warnings", *([f"- {x}" for x in warnings] or ["- None"]),"","## Safety note",report.safety_note,"","## Next manual review","阶段三十六：小资金灰度准入复核 / 人工决策包。"]
    return "\n".join(lines)+"\n"
def format_gray_rehearsal_report_json(report): return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
