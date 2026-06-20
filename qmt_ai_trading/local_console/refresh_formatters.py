from __future__ import annotations
import json
from .refresh_models import *

def _bul(xs): return '\n'.join(f'- {x}' for x in xs) or '- None'
def format_json_md(title, payload): return f'# {title}\n\n```json\n{payload}\n```\n'
def format_local_console_refresh_report_md(r):
    ev='\n'.join(f'- {e.stage}: {e.status.value} decision={e.decision} critical={e.critical_count} source={e.path}' for e in r.evidence) or '- None'
    routes='\n'.join(f'- {x.hash_route}: allowed={x.allowed} {x.title}' for x in r.routes)
    findings='\n'.join(f'- {x.severity.value} marker {x.marker} in {x.path}' for x in r.safety_findings) or '- None'
    return f'''# Stage68 Local Console Refresh and Navigation Layer

## Decision
{r.decision.value}

## Safety Note
本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。
READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW 只表示本地控制台刷新与导航增强层材料可供人工复核。

## Evidence Summary
{ev}

## Refresh Capability
{_bul([f.name for f in r.features])}

## Navigation Route Map
{routes}

## Read-only Refresh Action
- {r.refresh_action.name}: sources={', '.join(r.refresh_action.allowed_sources)} read_only={r.refresh_action.read_only}

## Data Bundle Reload
- reloadDataBundle() 只重新读取本地相对 JSON bundle。

## Last Updated Display
- updateLastLoadedAt() 将最新本地加载时间写入页面 time 元素。

## Loading State
- Loading State placeholder retained.

## Error State
- Forbidden hash route displays read-only error placeholder.

## Empty State
- Empty data renders local read-only empty placeholder.

## Frontend Safety Report
{findings}

## Forbidden Hash Routes
{_bul(['#/order','#/orders','#/trade','#/execute','#/approve','#/live','#/notify','#/account','#/positions','#/assets'])}

## Forbidden JS Actions
{_bul(["fetch('/order')","fetch('/trade')","fetch('/approve')","fetch('/account')","XMLHttpRequest","requests.post","webhook","smtp","sendMessage"])}

## Stage67 Preview Evidence
- Stage67 preview report is read if available; NO_GO or critical findings block Stage68.

## Stage66 Binding Evidence
- Stage66 binding data bundle is used as local read-only data source if available.

## Stage65 Shell Evidence
- Stage65 static shell asset pattern is extended without trading actions.

## Tolerant Reader / Encoding Summary
- Missing or invalid upstream JSON becomes warning evidence, not executable behavior.

## Roadmap Stage Plan Evidence
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
- Stage61-75 UI 产品化路线继续保留；UI 不能绕过 Risk Gate / Human Approval / 不能直接访问 QMT / 不能自动 approve。

## Required Manual Confirmations
- 人工复核本地控制台刷新与导航增强层材料。
- 确认 READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW 不是实盘授权。

## Blocking Reasons
{_bul(r.blocking_reasons)}

## Warnings
{_bul(r.warnings)}

## Next Stage Preview
Stage69 进入本地控制台状态分组与筛选体验层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
'''
