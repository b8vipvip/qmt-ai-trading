from __future__ import annotations
from .detail_models import *
def _bul(xs): return '\n'.join(f'- {x}' for x in xs) if xs else '- None'
def format_detail_report_md(r: LocalConsoleDetailReport):
    ev='\n'.join(f'- {e.stage}: {e.status.value} severity={e.severity.value} decision={e.decision} critical={e.critical_count} path={e.path}' for e in r.evidence) or '- None'
    routes=_bul(r.route_index); filters=_bul([f'{k}: {v}' for k,v in r.filter_index.items()])
    return f'''# Stage63 Local Console Detail and Filter Layer

## Decision
{r.decision.value}

## Safety Note
{r.safety_note}

## Evidence Summary
{ev}

## Console Detail Capability
- read-only report detail models
- stage/status/severity filters
- warning/blocking reason filters
- manifest and latest validation summaries

## Detail Route Index
{routes}

## Filter Index
{filters}

## Report Detail Summary
{ev}

## Stage62 Local Console Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage62'),'UNAVAILABLE')}

## Stage61 API Gateway Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage61'),'UNAVAILABLE')}

## Stage60 Pre-gray Final Review Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage60'),'UNAVAILABLE')}

## Stage59 Read-only Seal Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage59'),'UNAVAILABLE')}

## Stage58 Final Approval Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage58'),'UNAVAILABLE')}

## Stage57 Gray Candidate Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage57'),'UNAVAILABLE')}

## Stage56 Real Cache Quality Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage56'),'UNAVAILABLE')}

## Stage55 QMT Dry-run Calibration Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage55'),'UNAVAILABLE')}

## Warning Filter Results
{_bul(r.warnings)}

## Blocking Reason Filter Results
{_bul(r.blocking_reasons)}

## Manifest Detail
{r.filter_index.get('manifest')}

## Validation Log Detail
encoding={r.validation_detail.encoding}\npath={r.validation_detail.path}\n{r.validation_detail.summary}

## Scheduler Preview Detail
preview only; read_only=True / dry_run_only=True / no_trade_authorization=True / no_task_registered=True

## Safety Boundary Detail
read_only={r.safety_detail.read_only}; dry_run_only={r.safety_detail.dry_run_only}; no_trade_authorization={r.safety_detail.no_trade_authorization}

## Forbidden Console Detail Routes
{_bul(r.safety_detail.forbidden_routes)}

## Roadmap Stage Plan Evidence
完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
Stage61-75：API Gateway / 本地控制台 / UI 产品化路线；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## Required Manual Confirmations
- 人工复核 Stage63 本地控制台报告详情页与过滤层材料。

## Blocking Reasons
{_bul(r.blocking_reasons)}

## Warnings
{_bul(r.warnings)}

## Next Stage Preview
Stage64 进入本地控制台概览面板层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
'''
def format_filter_index_md(r): return '# Stage63 Filter Index\n\n'+_bul([f'{k}: {v}' for k,v in r.filters.items()])+'\n'
def format_warnings_md(r): return '# Stage63 Warning Filter Results\n\n'+_bul([f'{i.stage}: {i.message}' for i in r.items])+'\n'
def format_blocking_md(r): return '# Stage63 Blocking Reason Filter Results\n\n'+_bul([f'{i.stage}: {i.message}' for i in r.items])+'\n'
def format_manifest_md(r): return '# Stage63 Manifest Detail\n\n'+_bul([f'{i.stage}: {i.path} {i.status.value}' for i in r.items])+'\n'
def format_validation_md(r): return f'# Stage63 Validation Log Detail\n\n- status={r.detail.status.value}\n- encoding={r.detail.encoding}\n- path={r.detail.path}\n\n```text\n{r.detail.summary}\n```\n'
def format_next_overview_plan_md(r): return '# Stage64 Next Console Overview Plan\n\n## Safety Note\n'+r.safety_note+'\n\n'+_bul(r.items)+'\n'
