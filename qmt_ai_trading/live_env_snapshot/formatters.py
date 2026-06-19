# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from .models import LiveEnvSnapshotCategory as C, LiveEnvSnapshotReport, ReadonlyEnvironmentSnapshotReport, enum_value, to_plain

def _rows(items):
    rows=[]
    for x in items:
        summary=getattr(x,'summary','') or getattr(x,'message','') or 'No details provided.'
        rows.append(f"| {enum_value(getattr(x,'severity',''))} | {enum_value(getattr(x,'status',''))} | {enum_value(getattr(x,'category',''))} | {getattr(x,'path','')} | {getattr(x,'name',getattr(x,'title',''))} | {getattr(x,'value','')} | {summary} |")
    return rows

def format_live_env_snapshot_report_markdown(report: LiveEnvSnapshotReport) -> str:
    ev=report.evidence
    def cat(c): return [x for x in ev if enum_value(x.category)==enum_value(c)]
    lines=["# Stage44 Live Environment Snapshot and Config Freeze Review","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"READY_FOR_ENV_SNAPSHOT 只表示环境快照材料可供人工复核，不是实盘授权。","","## Evidence Summary",json.dumps(report.summary, ensure_ascii=False),"","| Severity | Status | Category | Path | Name/Title | Value | Summary |","| --- | --- | --- | --- | --- | --- | --- |"]
    lines += _rows(ev) or ["| WARN | SKIPPED | SYSTEM | | None | | No evidence collected |"]
    for c,title in [(C.STAGE40_REDLINE_REVIEW,"Stage40 Red-line Review Evidence"),(C.STAGE41_LEDGER,"Stage41 Ledger Evidence"),(C.STAGE42_HUMAN_REVIEW,"Stage42 Human Review Evidence"),(C.STAGE43_SIGNATURE_FREEZE,"Stage43 Signature Freeze Evidence")]:
        lines += ["", f"## {title}"] + ([f"- {enum_value(x.status)} {x.path}: {x.summary}" for x in cat(c)] or ["- Not found / skipped."])
    lines += ["","## Config Freeze Review","| Severity | Status | Category | Path | Name | Value | Summary |","| --- | --- | --- | --- | --- | --- | --- |"] + _rows(report.config_freeze_review)
    lines += ["","## Read-only Environment Snapshot","| Severity | Status | Category | Path | Name | Value | Summary |","| --- | --- | --- | --- | --- | --- | --- |"] + _rows(report.environment_snapshot)
    lines += ["","## Runtime Artifact Ignore Review"] + [f"- {x.name}: {enum_value(x.status)} — {x.summary}" for x in report.config_freeze_review if enum_value(x.category)==enum_value(C.CONFIG_FREEZE) and (str(x.name).endswith('/') or 'gitignore' in x.item_id)]
    lines += ["","## Required Manual Confirmations"] + [f"- [ ] {x}" for x in report.required_manual_confirmations]
    lines += ["","## Blocking Reasons"] + ([f"- {x}" for x in report.blocking_reasons if x] or ["- None"])
    lines += ["","## Warnings"] + ([f"- {x}" for x in report.warnings if x] or ["- None"])
    lines += ["","## Next Stage Preview","Stage45 仍不得直接实盘；只能继续做灰度前只读运行手册、人工确认流程演练或更严格的配置冻结复核。",""]
    return "\n".join(lines)

def format_readonly_environment_snapshot_markdown(report: ReadonlyEnvironmentSnapshotReport) -> str:
    lines=["# Stage44 Read-only Environment Snapshot","","## Decision",str(enum_value(report.decision)),"","## Safety Note",report.safety_note,"READY_FOR_ENV_SNAPSHOT 只表示环境快照材料可供人工复核，不是实盘授权。","","## Snapshot Items","| Severity | Status | Category | Path | Name | Value | Summary |","| --- | --- | --- | --- | --- | --- | --- |"]
    lines += _rows(report.items) or ["| WARN | SKIPPED | SYSTEM | | None | | No snapshot items |"]
    lines += ["","## Blocking Reasons"] + ([f"- {x}" for x in report.blocking_reasons if x] or ["- None"])
    lines += ["","## Warnings"] + ([f"- {x}" for x in report.warnings if x] or ["- None"])
    return "\n".join(lines)+"\n"

def format_live_env_snapshot_report_json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
def format_readonly_environment_snapshot_report_json(report): return json.dumps(to_plain(report), ensure_ascii=False, indent=2, default=str)
