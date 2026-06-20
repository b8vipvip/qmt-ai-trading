from __future__ import annotations
from .shell_models import *
def _bul(xs): return '\n'.join(f'- {x}' for x in xs) if xs else '- None'
def format_shell_report_md(r):
    ev=_bul([f'{e.stage}: {e.status.value} decision={e.decision} critical={e.critical_count} path={e.path} summary={e.summary}' for e in r.evidence])
    return f'''# Stage65 Local Console Shell / Static Page Skeleton

## Decision
{r.decision.value}

## Safety Note
{r.safety_note}

## Evidence Summary
{ev}

## Shell Capability
- 本地只读静态页面骨架
- read_only=True
- dry_run_only=True
- no_trade_authorization=True

## Static Assets
{_bul([f'{a.name}: {a.path} {a.asset_type.value}' for a in r.assets])}

## Shell Route Map
{_bul([x.path for x in r.routes])}

## Data Binding Placeholders
{_bul([f'{p.placeholder_id}: {p.source} -> {p.target_selector}' for p in r.data_binding_placeholders])}

## Static Safety Boundary
- 不调用 xttrader
- 不下单
- 不查询真实账户
- 不发送真实通知
- 不自动 approve

## Dashboard Placeholder
Stage64 dashboard cards placeholder.

## Report List Placeholder
Stage62 report list placeholder.

## Report Detail Placeholder
Stage63 report detail placeholder.

## Filter Placeholder
Stage63 filter placeholder.

## Manifest Placeholder
shell_manifest.json placeholder.

## Validation Placeholder
Latest validation summary placeholder; encoding warning may be displayed but is non-blocking.

## Scheduler Placeholder
Scheduler preview only; no_task_registered=True.

## API Capability Placeholder
Stage61 read-only API capability placeholder.

## Stage64 Dashboard Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage64'),'UNAVAILABLE')}

## Stage63 Detail Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage63'),'UNAVAILABLE')}

## Stage62 Console Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage62'),'UNAVAILABLE')}

## Stage61 API Gateway Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage61'),'UNAVAILABLE')}

## Tolerant Reader Summary
JSON 优先；失败降级 Markdown；encoding warning 仅 WARN，不作为 CRITICAL。

## Forbidden Shell Routes
#/order #/orders #/trade #/execute #/approve #/live #/notify #/account #/positions #/assets are forbidden.

## Forbidden JS Actions
fetch('/order'), fetch('/trade'), fetch('/approve'), fetch('/account'), fetch('/positions'), XMLHttpRequest and real notification actions are forbidden.

## Roadmap Stage Plan Evidence
完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
Stage61-75：API Gateway / 本地控制台 / UI 产品化路线；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## Required Manual Confirmations
- 人工复核 Stage65 本地控制台 shell / 静态页面骨架层材料。
- 确认 READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW 不是实盘授权。

## Blocking Reasons
{_bul(r.blocking_reasons)}

## Warnings
{_bul(r.warnings)}

## Next Stage Preview
Stage66 进入本地控制台静态数据绑定层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
'''
def format_manifest_md(r): return '# Stage65 Shell Manifest\n\n'+_bul([f'{a.name}: {a.sha256}' for a in r.assets])+'\n'
def format_route_map_md(r): return '# Stage65 Shell Route Map\n\n'+_bul([f'{x.path}: {x.title} read_only={x.read_only}' for x in r.routes])+'\n'
def format_asset_index_md(r): return '# Stage65 Shell Asset Index\n\n'+_bul([f'{a.name}: {a.path} {a.asset_type.value}' for a in r.assets])+'\n'
def format_binding_md(r): return '# Stage65 Data Binding Placeholders\n\n'+_bul([f'{p.placeholder_id}: {p.source} -> {p.target_selector}; {p.stage66_binding_plan}' for p in r.placeholders])+'\n'
def format_safety_md(r): return '# Stage65 Static Safety Boundary\n\n'+_bul(r.items)+f'\n\nread_only={r.read_only}\ndry_run_only={r.dry_run_only}\nno_trade_authorization={r.no_trade_authorization}\nno_task_registered={r.no_task_registered}\n'
def format_plan_md(r): return f'# Stage66 Console Data Binding Plan\n\n## Safety Note\n{r.safety_note}\n\n## Items\n{_bul(r.items)}\n'
