# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from .models import LiveSignatureFreezeCategory as C, ConfigFreezeReport, LiveSignatureFreezeReport, enum_value, to_plain

def _rows(items):
    return [f"| {enum_value(x.severity)} | {enum_value(x.status)} | {enum_value(x.category)} | {getattr(x,'path','')} | {getattr(x,'title',getattr(x,'marker',''))} | {getattr(x,'summary',getattr(x,'message',''))} |" for x in items]

def format_live_signature_freeze_report_markdown(report: LiveSignatureFreezeReport) -> str:
    ev=report.evidence
    def cat(c): return [x for x in ev if enum_value(x.category)==enum_value(c)]
    lines=["# Stage43 Live Signature Checklist and Config Freeze","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"READY_FOR_SIGNATURE 只表示材料可供人工签字复核，不是实盘授权。","","## Evidence Summary",json.dumps(report.summary, ensure_ascii=False),"","| Severity | Status | Category | Path | Title | Summary |","| --- | --- | --- | --- | --- | --- |"]
    lines += _rows(ev) or ["| WARN | SKIPPED | SYSTEM | | None | No evidence collected |"]
    for c,title in [(C.STAGE40_REDLINE_REVIEW,"Stage40 Red-line Review Evidence"),(C.STAGE41_LEDGER,"Stage41 Ledger Evidence"),(C.STAGE42_HUMAN_REVIEW,"Stage42 Human Review Evidence")]:
        lines += ["", f"## {title}"] + ([f"- {enum_value(x.status)} {x.path}: {x.summary}" for x in cat(c)] or ["- Not found / skipped."])
    lines += ["","## Signature Checklist","- [ ] 确认 Stage43 不等于实盘授权。","- [ ] 确认 READY_FOR_SIGNATURE 只表示材料可供人工签字复核。","- [ ] 确认未调用 xttrader、未下单、未查询真实账户、未发送真实通知。","- [ ] 确认 Risk Gate 与 Human Approval 不可绕过。"]
    lines += ["","## Config Freeze Summary"] + ([f"- {x.name}: {x.frozen_value} — {x.summary}" for x in report.config_freeze_items] or ["- Config freeze summary will be generated with the same read-only boundary."])
    lines += ["","## Required Manual Sign-offs"] + [f"- [ ] {x}" for x in report.required_manual_signoffs]
    lines += ["","## Blocking Reasons"] + ([f"- {x}" for x in report.blocking_reasons] or ["- None"])
    lines += ["","## Warnings"] + ([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["","## Next Stage Preview","Stage44 仍不得直接实盘；只能继续做配置封存复核、人工签字校验、只读环境快照或更严格的灰度前检查。",""]
    return "\n".join(lines)

def format_config_freeze_report_markdown(report: ConfigFreezeReport) -> str:
    lines=["# Stage43 Config Freeze Summary","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"","## Frozen Items"]
    lines += [f"- {x.name}: {x.frozen_value} — {x.summary}" for x in report.items] or ["- No config freeze items."]
    lines += ["","## Blocking Reasons"] + ([f"- {x}" for x in report.blocking_reasons] or ["- None"])
    lines += ["","## Warnings"] + ([f"- {x}" for x in report.warnings] or ["- None"])
    lines += ["","## Summary",json.dumps(report.summary, ensure_ascii=False),""]
    return "\n".join(lines)

def format_live_signature_freeze_report_json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
def format_config_freeze_report_json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
