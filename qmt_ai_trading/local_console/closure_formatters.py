from __future__ import annotations
import json
from .closure_models import *

def format_json_md(title, body): return f'# {title}\n\n```json\n{body}\n```\n'
def format_ui_productization_closure_report_md(r: UiProductizationClosureReport):
    def bullets(items, attr='title'):
        return '\n'.join(f'- {getattr(x,attr,str(x))}: {getattr(x,"note",getattr(x,"safety_note",getattr(x,"recommendation","")))}' for x in items) or '- N/A'
    return f'''# Stage75 UI Productization Closure Layer

## Decision
{r.decision.value}

## Safety Note
本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。
READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW 只表示 UI 产品化收口层材料可供人工复核。
closure report / capability matrix / final conclusion draft 都不是审批授权。

## Evidence Summary
{bullets(r.evidence,'stage')}

## Stage Overview
{bullets(r.stage_overview,'stage')}

## UI Capability Matrix
{bullets(r.capability_matrix,'capability')}

## Safety Boundary Table
{bullets(r.safety_boundary_table,'boundary')}

## Read-only Demo Entry
{bullets(r.readonly_demo_entry,'entry')}

## Route Coverage Summary
{bullets(r.route_coverage_summary,'route')}

## Asset Coverage Summary
{bullets(r.asset_coverage_summary,'file_name')}

## Risk and Limitation Summary
{bullets(r.risk_limitation_summary,'risk')}

## Final Acceptance Conclusion Draft
{r.final_acceptance_conclusion_draft.conclusion}

## Future Roadmap Recommendation
{bullets(r.future_roadmap_recommendation,'stage')}

## Closure Safety Report
critical_count={r.summary.get('critical_count',0)}

## Forbidden Hash Routes
#/order #/orders #/trade #/execute #/approve #/approval #/auto-approve #/live #/notify #/account #/positions #/assets

## Forbidden JS Actions
No executable forbidden JS actions are allowed; app.js only fetches local relative JSON files.

## Stage74 Demo Package Evidence
Stage74 READY evidence is required before READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW.

## Stage73 Help Docs Evidence
Read-only help docs evidence is referenced when present.

## Stage72 UI Acceptance Evidence
Read-only UI acceptance evidence is referenced when present.

## Roadmap Stage Plan Evidence
完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
Stage61-75 前端 UI 产品化计划继续保留；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## Required Manual Confirmations
- 人工确认 Stage75 只读材料可复核。
- 人工确认 Stage76 先做路线重审，不直接进入实盘。

## Blocking Reasons
{chr(10).join('- '+x for x in r.blocking_reasons) or '- N/A'}

## Warnings
{chr(10).join('- '+x for x in r.warnings) or '- N/A'}

## Encoding / UTF-8 Check
Markdown/JSON 使用 UTF-8，json.dumps 使用 ensure_ascii=False，不输出 NUL 或 mojibake。

## Next Stage Preview
Stage75 是 Stage61-75 UI 产品化路线收口层；通过后建议先做路线重审，不直接进入实盘。
'''
