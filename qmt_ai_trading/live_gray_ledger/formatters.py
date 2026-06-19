from __future__ import annotations
import json
from .models import LiveGrayLedgerCategory as C, LiveGrayLedgerReport, enum_value, to_plain

def _rows(items):
    return [f"| {enum_value(x.severity)} | {enum_value(x.status)} | {enum_value(x.category)} | {x.path} | {x.title or x.marker} | {x.summary if hasattr(x,'summary') else x.message} |" for x in items]

def format_live_gray_ledger_report_markdown(report: LiveGrayLedgerReport) -> str:
    ev=report.evidence
    def cat(c): return [x for x in ev if enum_value(x.category)==enum_value(c)]
    lines=["# Stage41 Live Gray Read-only Ledger","", "## Decision", str(enum_value(report.decision)), "", "## Safety Note", report.safety_note, "", "## Evidence Summary", json.dumps(report.summary, ensure_ascii=False), "", "| Severity | Status | Category | Path | Title | Summary |", "| --- | --- | --- | --- | --- | --- |"]
    lines += _rows(ev) or ["| WARN | SKIPPED | SYSTEM | | None | No evidence collected |"]
    sections=[(C.STAGE37_MANUAL_PREP,"Stage37 Manual Prep Evidence"),(C.STAGE38_ENV_CHECK,"Stage38 Live Env Check Evidence"),(C.STAGE39_FINAL_AUTHORIZATION,"Stage39 Final Authorization Evidence"),(C.STAGE40_REDLINE_REVIEW,"Stage40 Red-line Review Evidence")]
    for c,title in sections:
        lines += ["", f"## {title}"] + ([f"- {enum_value(x.status)} {x.path}: {x.summary}" for x in cat(c)] or ["- Not found / skipped."])
    lines += ["", "## Human Review Checklist", "- [ ] 确认 READY_FOR_MANUAL_REVIEW 只表示材料可供人工复核，不是实盘授权。", "- [ ] 确认本阶段不批准、不下单、不注册真实任务、不发送真实通知。", "- [ ] 确认 Risk Gate 与 Human Approval 仍是未来阶段必须边界。", "", "## Blocking Reasons"]
    lines += [f"- {x}" for x in report.blocked_reasons] or ["- None"]
    lines += ["", "## Warnings"] + ([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["", "## Next Stage Preview", "Stage42 仍然只能做更严格的人工复核/只读模拟，不得直接实盘。", ""]
    return "\n".join(lines)

def format_live_gray_ledger_report_json(report: LiveGrayLedgerReport) -> str:
    return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
