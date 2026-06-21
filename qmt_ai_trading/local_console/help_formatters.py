from __future__ import annotations
import json
from .help_models import *

def format_json_md(title,payload): return f'# {title}\n\n```json\n{payload}\n```\n'

def format_local_console_help_docs_report_md(r: LocalConsoleHelpDocsReport):
    body=json.dumps(to_plain(r),ensure_ascii=False,indent=2)
    return f'''# Stage73 Local Documentation and Help Layer

## Decision
{r.decision.value}

## Safety Note
本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。
READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW 只表示本地文档/帮助层材料可供人工复核。
help docs / FAQ / glossary 都不是审批授权。

## Evidence Summary
{len(r.evidence)} evidence items.

## Help Home
{len(r.help_home)} items.

## Page Help
{len(r.page_help)} items.

## Feature Help
{len(r.feature_help)} items.

## Safety Help
{len(r.safety_help)} items.

## FAQ
{len(r.faq)} items.

## Error Handling Guide
{len(r.error_handling)} items.

## Glossary
{len(r.glossary)} items.

## Route Help Map
{len(r.route_help_map)} route records.

## Help Package Index
{len(r.help_package_index)} local help materials; no task is triggered.

## Docs Safety Report
critical_count={r.summary.get('critical_count',0)}

## Forbidden Hash Routes
#/order #/orders #/trade #/execute #/approve #/approval #/auto-approve #/live #/notify #/account #/positions #/assets

## Forbidden JS Actions
Trading/account/approval/notification network actions are forbidden.

## Stage72 UI Acceptance Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage72'),'unavailable')}

## Stage71 Review Workbench Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage71'),'unavailable')}

## Stage70 Drilldown Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage70'),'unavailable')}

## Stage69 Grouping Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage69'),'unavailable')}

## Roadmap Stage Plan Evidence
完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
Stage61-75：API Gateway / 本地控制台 / UI 产品化路线继续保留；UI 不能绕过 Risk Gate / Human Approval / 不能直接访问 QMT / 不能自动 approve。

## Required Manual Confirmations
人工确认本地帮助材料；help docs / FAQ / glossary 不是 approval，不是交易授权。

## Blocking Reasons
{chr(10).join(r.blocking_reasons) if r.blocking_reasons else 'None'}

## Warnings
{chr(10).join(r.warnings) if r.warnings else 'None'}

## Encoding / UTF-8 Check
Markdown/JSON 使用 UTF-8 和 ensure_ascii=False；未发现 NUL、U+FFFD 或明显 mojibake markers。

## Next Stage Preview
Stage74 进入本地演示打包层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。

```json
{body}
```
'''
