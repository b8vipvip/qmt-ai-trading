from __future__ import annotations
from .models import *
def _bul(xs): return '\n'.join(f'- {x}' for x in xs) if xs else '- None'
def format_console_index_md(r): return '# Stage62 Console Route Index\n\n'+'\n'.join(f'- {x.method} {x.path} read_only={x.read_only}' for x in r.routes)+'\n'
def format_report_list_md(r): return '# Stage62 Console Report List\n\n'+'\n'.join(f'- {x.stage}: {x.title} ({x.path})' for x in r.items)+'\n'
def format_console_safety_md(r):
    b=r.boundary; return '# Stage62 Console Safety Boundary\n\n'+_bul(b.items)+f'\n\n- read_only={b.read_only}\n- dry_run_only={b.dry_run_only}\n- no_trade_authorization={b.no_trade_authorization}\n- no_task_registered={b.no_task_registered}\n\n## Forbidden Console Routes\n'+_bul(b.forbidden_routes)+'\n'
def format_next_plan_md(r): return '# Stage63 Next Console Detail Plan\n\n## Safety Note\n'+r.safety_note+'\n\n'+_bul(r.items)+'\n'
def format_local_console_report_md(r):
    ev='\n'.join(f'- {e.category.value}: {e.status.value} {e.title} - {e.summary}' for e in r.evidence) or '- None'
    routes='\n'.join(f'- GET {x.path}' for x in r.route_index)
    reports='\n'.join(f'- {x.stage}: {x.title}' for x in r.report_list)
    safety=_bul(r.safety_boundary.items)
    return f'''# Stage62 Local Console Report Reader Layer

## Decision
{r.decision.value}

## Safety Note
{r.safety_note}

## Evidence Summary
{ev}

## Console Capability
- local read-only report browsing
- route/index/report generation for Stage63

## Console Route Index
{routes}

## Report List
{reports}

## Stage61 API Gateway Evidence
{next((e.summary for e in r.evidence if e.category==LocalConsoleCategory.STAGE61_API_GATEWAY),'UNAVAILABLE')}

## Stage60 Pre-gray Final Review Evidence
{next((e.summary for e in r.evidence if e.category==LocalConsoleCategory.STAGE60_PRE_GRAY_FINAL_REVIEW),'UNAVAILABLE')}

## Stage59 Read-only Seal Evidence
{next((e.summary for e in r.evidence if e.category==LocalConsoleCategory.STAGE59_READONLY_SEAL),'UNAVAILABLE')}

## Stage58 Final Approval Evidence
{next((e.summary for e in r.evidence if e.category==LocalConsoleCategory.STAGE58_FINAL_APPROVAL),'UNAVAILABLE')}

## Stage57 Gray Candidate Evidence
{next((e.summary for e in r.evidence if e.category==LocalConsoleCategory.STAGE57_GRAY_CANDIDATE),'UNAVAILABLE')}

## Stage56 Real Cache Quality Evidence
{next((e.summary for e in r.evidence if e.category==LocalConsoleCategory.STAGE56_REAL_CACHE_QUALITY),'UNAVAILABLE')}

## Stage55 QMT Dry-run Calibration Evidence
{next((e.summary for e in r.evidence if e.category==LocalConsoleCategory.STAGE55_QMT_DRYRUN_CALIBRATION),'UNAVAILABLE')}

## Latest Validation Summary
{r.validation_summary}

## Manifest Summary
{r.manifest_summary}

## Scheduler Preview Summary
{r.scheduler_preview_summary}

## Safety Boundary
{safety}

## Forbidden Console Routes
{_bul(r.safety_boundary.forbidden_routes)}

## Roadmap Stage Plan Evidence
完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
Stage61-75：API Gateway / 本地控制台 / UI 产品化路线；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## Required Manual Confirmations
- 人工复核 Stage62 报告读取层材料。

## Blocking Reasons
{_bul(r.blocking_reasons)}

## Warnings
{_bul(r.warnings)}

## Next Stage Preview
Stage63 进入本地控制台报告详情页与过滤层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
'''
