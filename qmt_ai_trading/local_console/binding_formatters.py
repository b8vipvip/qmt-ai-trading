from __future__ import annotations
from .binding_models import *
def _bul(xs): return '\n'.join(f'- {x}' for x in xs) if xs else '- None'
def format_json_md(title,obj): return f'# {title}\n\n```json\n{obj}\n```\n'
def format_binding_report_md(r):
    ev=_bul([f'{e.stage}: {e.status.value} decision={e.decision} critical={e.critical_count} path={e.path} summary={e.summary}' for e in r.evidence])
    return f'''# Stage66 Local Console Static Data Binding Layer

## Decision
{r.decision.value}

## Safety Note
{r.safety_note}

## Evidence Summary
{ev}

## Binding Capability
- 静态页面数据绑定 manifest
- dashboard/report/detail/API/scheduler/safety/validation/manifest/hash 数据绑定
- read_only=True
- dry_run_only=True
- no_trade_authorization=True

## Static Bound Assets
{_bul([a.get('name','') for a in r.assets])}

## Data Bundle
Stage66 data_bundle.json includes metadata, dashboard, report_list, detail_filters, api_capability, scheduler_preview, safety_boundary.

## Binding Manifest
binding_manifest.json records source path, source type, target section id, status, severity, encoding, fallback_used and safety flags.

## Data Source Map
{_bul([f'{k} -> {v}' for k,v in r.data_source_map.items()])}

## Missing Data Placeholders
{_bul([f'{p.source_path} -> {p.target_section_id}' for p in r.placeholders])}

## Dashboard Data Binding
Stage64 dashboard cards are bound to #dashboard-overview-section.

## Report List Data Binding
Stage62 report list is bound to #report-list-section.

## Detail Filter Data Binding
Stage63 filter_index is bound to #detail-filter-section.

## API Capability Data Binding
Stage61 API Gateway capability is bound to #api-capability-section.

## Scheduler Preview Data Binding
Scheduler preview status is bound read-only.

## Safety Boundary Data Binding
Safety boundary is fixed read-only and no_trade_authorization=True.

## Validation Summary Data Binding
Latest validation log summary is decoded without NUL/BOM display.

## Manifest / Hash Data Binding
Stage64 manifest hash status is bound to #manifest-section.

## Stage65 Shell Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage65'),'UNAVAILABLE')}

## Stage64 Dashboard Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage64'),'UNAVAILABLE')}

## Stage63 Detail Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage63'),'UNAVAILABLE')}

## Stage62 Console Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage62'),'UNAVAILABLE')}

## Stage61 API Gateway Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage61'),'UNAVAILABLE')}

## Tolerant Reader / Encoding Summary
JSON 优先；JSON 失败读取 Markdown；自动识别 UTF-8 / UTF-8-SIG / UTF-16 / UTF-16LE / UTF-16BE；摘要无 NUL/BOM；乱码仅显示 encoding_warning=True。

## Forbidden Binding Routes
#/order #/orders #/trade #/execute #/approve #/live #/notify #/account #/positions #/assets are forbidden.

## Forbidden JS Actions
fetch('/order'), fetch('/trade'), fetch('/approve'), fetch('/account'), fetch('/positions'), XMLHttpRequest and real notification actions are forbidden.

## Roadmap Stage Plan Evidence
完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
Stage61-75：API Gateway / 本地控制台 / UI 产品化路线；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## Required Manual Confirmations
- 人工复核 Stage66 本地控制台静态数据绑定层材料。
- 确认 READY_FOR_LOCAL_CONSOLE_BINDING_REVIEW 不是实盘授权。

## Blocking Reasons
{_bul(r.blocking_reasons)}

## Warnings
{_bul(r.warnings)}

## Next Stage Preview
Stage67 进入本地只读预览服务层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
'''
