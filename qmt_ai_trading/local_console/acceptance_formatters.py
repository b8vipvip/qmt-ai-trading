from __future__ import annotations
import json
from .acceptance_models import *

def format_json_md(title,payload): return f'# {title}\n\n```json\n{payload}\n```\n'

def format_local_console_ui_acceptance_report_md(r: LocalConsoleUiAcceptanceReport):
    body=json.dumps(to_plain(r),ensure_ascii=False,indent=2)
    return f'''# Stage72 Local Console UI Acceptance Summary Layer

## Decision
{r.decision.value}

## Safety Note
本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。
READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW 只表示本地控制台 UI 验收汇总层材料可供人工复核。
UI acceptance summary / acceptance conclusion draft 都不是审批授权。

## Evidence Summary
{len(r.evidence)} evidence items.

## UI Acceptance Summary
{r.ui_summary.note}

## Page Inventory
{len(r.page_inventory)} pages.

## Feature Inventory
{len(r.feature_inventory)} features.

## Safety Checklist
{len(r.safety_checklist)} safety items.

## Open Items
{len(r.open_items)} open items.

## Route Coverage
{len(r.route_coverage)} route records.

## Asset Coverage
{len(r.asset_coverage)} asset records.

## Acceptance Conclusion Draft
{r.conclusion_draft.draft}

## Acceptance Package Index
{len(r.package_index)} local acceptance materials; no task is triggered.

## UI Acceptance Safety Report
critical_count={r.summary.get('critical_count',0)}

## Forbidden Hash Routes
#/order #/orders #/trade #/execute #/approve #/approval #/auto-approve #/live #/notify #/account #/positions #/assets

## Forbidden JS Actions
Trading/account/approval/notification network actions are forbidden.

## Stage71 Review Workbench Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage71'),'unavailable')}

## Stage70 Drilldown Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage70'),'unavailable')}

## Stage69 Grouping Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage69'),'unavailable')}

## Stage68 Refresh Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage68'),'unavailable')}

## Roadmap Stage Plan Evidence
完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
Stage61-75：API Gateway / 本地控制台 / UI 产品化路线继续保留；UI 不能绕过 Risk Gate / Human Approval / 不能直接访问 QMT / 不能自动 approve。

## Required Manual Confirmations
人工确认 UI 验收汇总材料，不代表实盘授权。

## Blocking Reasons
{chr(10).join(r.blocking_reasons) if r.blocking_reasons else 'None'}

## Warnings
{chr(10).join(r.warnings) if r.warnings else 'None'}

## Next Stage Preview
Stage73 进入本地文档/帮助层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。

```json
{body}
```
'''
