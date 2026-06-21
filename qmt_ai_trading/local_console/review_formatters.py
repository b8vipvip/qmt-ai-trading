from __future__ import annotations
import json
from .review_models import *

def format_json_md(title: str, payload: str) -> str:
    return f"# {title}\n\n```json\n{payload}\n```\n"

def _bullets(items): return '\n'.join(f'- {x}' for x in items) or '- None'

def format_local_console_review_workbench_report_md(r: LocalConsoleReviewWorkbenchReport) -> str:
    evidence='\n'.join(f"- {e.stage}: status={e.status.value} decision={e.decision} critical_count={e.critical_count} path={e.path}" for e in r.evidence) or '- None'
    checklist='\n'.join(f"- {i.item_id}: {i.title} ({i.state.value}) - {i.note}" for i in r.checklist) or '- None'
    confirmations='\n'.join(f"- {i.item_id}: {i.title} - {i.note}" for i in r.confirmations) or '- None'
    package='\n'.join(f"- {i.file_name}: {i.title} - {i.note}" for i in r.package_index) or '- None'
    safety='\n'.join(f"- {f.severity.value}: {f.marker} in {f.path} - {f.note}" for f in r.safety_findings) or '- None'
    return f"""# Stage71 Local Console Manual Review Workbench Layer

## Decision
{r.decision.value}

## Safety Note
本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。
READY_FOR_LOCAL_CONSOLE_REVIEW_WORKBENCH_REVIEW 只表示本地控制台人工复核工作台层材料可供人工复核。
review notes / checklist / local confirmations 都不是审批授权。

## Evidence Summary
{evidence}

## Review Workbench Capability
- 人工复核工作台页面、本地只读安全横幅、只读 hash route、Stage70 证据面板。

## Review Checklist
{checklist}

## Review Notes Template
{r.notes_template.body}

## Local Confirmation Checklist
{confirmations}

## Review Package Index
{package}

## Review Status Placeholder
{r.status_placeholder.state.value}: {r.status_placeholder.note}

## Review Conclusion Draft
{r.conclusion_draft.draft}

## Review Safety Report
{safety}

## Forbidden Hash Routes
- #/order #/orders #/trade #/execute #/approve #/approval #/auto-approve #/live #/notify #/account #/positions #/assets

## Forbidden JS Actions
- 交易、账户、审批、通知、自动批准相关 fetch/XMLHttpRequest/button/action 均禁止。

## Stage70 Drilldown Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage70'), 'UNAVAILABLE')}

## Stage69 Grouping Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage69'), 'UNAVAILABLE')}

## Stage68 Refresh Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage68'), 'UNAVAILABLE')}

## Stage67 Preview Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage67'), 'UNAVAILABLE')}

## Stage66 Binding Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage66'), 'UNAVAILABLE')}

## Roadmap Stage Plan Evidence
完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）已保留，Stage71 属于 Stage61-75。

## UI Productization Plan Evidence
UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## Required Manual Confirmations
{confirmations}

## Blocking Reasons
{_bullets(r.blocking_reasons)}

## Warnings
{_bullets(r.warnings)}

## Next Stage Preview
Stage72 进入本地控制台 UI 验收汇总层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
"""
