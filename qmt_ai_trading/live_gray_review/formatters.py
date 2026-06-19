# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from .models import LiveGrayReviewCategory as C, LiveGrayReviewReport, ReadOnlyRehearsalReport, enum_value, to_plain

def _rows(items):
    return [f"| {enum_value(x.severity)} | {enum_value(x.status)} | {enum_value(x.category)} | {x.path} | {x.title if hasattr(x,'title') else x.marker} | {x.summary if hasattr(x,'summary') else x.message} |" for x in items]

def format_live_gray_review_report_markdown(report: LiveGrayReviewReport) -> str:
    ev=report.evidence
    def cat(c): return [x for x in ev if enum_value(x.category)==enum_value(c)]
    lines=["# Stage42 Live Gray Human Review Package","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"","## Evidence Summary",json.dumps(report.summary, ensure_ascii=False),"","| Severity | Status | Category | Path | Title | Summary |","| --- | --- | --- | --- | --- | --- |"]
    lines += _rows(ev) or ["| WARN | SKIPPED | SYSTEM | | None | No evidence collected |"]
    for c,title in [(C.STAGE39_FINAL_AUTHORIZATION,"Stage39 Final Authorization Evidence"),(C.STAGE40_REDLINE_REVIEW,"Stage40 Red-line Review Evidence"),(C.STAGE41_LEDGER,"Stage41 Live Gray Ledger Evidence")]:
        lines += ["", f"## {title}"] + ([f"- {enum_value(x.status)} {x.path}: {x.summary}" for x in cat(c)] or ["- Not found / skipped."])
    rehearsal=report.rehearsal
    steps=[] if rehearsal is None or isinstance(rehearsal, dict) else rehearsal.steps
    lines += ["","## Read-only Rehearsal Summary"] + ([f"- {s.step_id}: {s.title} => {enum_value(s.status)}" for s in steps] or ["- readonly_rehearsal will be generated with the same read-only boundary."])
    lines += ["","## Human Go/No-Go Checklist","- [ ] 确认 Stage42 不等于实盘授权。","- [ ] 确认 READY_FOR_HUMAN_REVIEW 只表示材料可供人工复核。","- [ ] 确认未调用 xttrader、未下单、未查询真实账户、未发送真实通知。","- [ ] 确认 Risk Gate 与 Human Approval 不可绕过。"]
    lines += ["","## Blocking Reasons"] + ([f"- {x}" for x in report.blocking_reasons] or ["- None"])
    lines += ["","## Warnings"] + ([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["","## Required Manual Sign-offs"] + [f"- [ ] {x}" for x in report.required_manual_signoffs]
    lines += ["","## Next Stage Preview","Stage43 仍不得直接实盘；只能继续做人工签字、只读演练、配置封存或更严格的灰度前检查。",""]
    return "\n".join(lines)

def format_readonly_rehearsal_report_markdown(report: ReadOnlyRehearsalReport) -> str:
    lines=["# Stage42 Read-only Rehearsal Package","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"","## Steps"]
    lines += [f"- {s.step_id}: {s.title} | status={enum_value(s.status)} | expected={s.expected_result}" for s in report.steps]
    lines += ["","## Summary",json.dumps(report.summary, ensure_ascii=False),""]
    return "\n".join(lines)

def format_live_gray_review_report_json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
def format_readonly_rehearsal_report_json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
