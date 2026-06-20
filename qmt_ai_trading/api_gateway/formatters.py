from __future__ import annotations
import json
from .models import *
def _bul(items): return '\n'.join(f'- {x}' for x in items) or '- None'
def format_route_index_md(idx):
    return '# Stage61 API Gateway Route Index\n\n## Read-only Routes\n'+'\n'.join(f'- {e.method} {e.path} read_only={e.read_only}' for e in idx.endpoints)+'\n\n## Forbidden Routes\n'+'\n'.join(f'- {e.method} {e.path} forbidden route' for e in idx.forbidden_routes)+'\n'
def format_safety_boundary_md(r): return '# Stage61 API Gateway Safety Boundary\n\n'+_bul(r.items)+'\n\n## Blocking Reasons\n'+_bul(r.blocking_reasons)+'\n\n## Warnings\n'+_bul(r.warnings)+'\n'
def format_stage_status_md(r): return f'# Stage61 Stage Status\n\n- current_stage: {r.current_stage}\n- stage_name: {r.stage_name}\n- previous_stage: {r.previous_stage}\n- next_stage: {r.next_stage}\n- read_only: {r.read_only}\n- dry_run_only: {r.dry_run_only}\n- no_trade_authorization: {r.no_trade_authorization}\n'
def format_next_ui_dashboard_plan_md(r): return '# Stage62 Next UI Dashboard Plan\n\n## Safety Note\n'+r.safety_note+'\n\n'+_bul(r.items)+'\n'
def format_api_gateway_report_md(r):
    ev='\n'.join(f'- {e.category.value}: {e.status.value} {e.title} {e.summary}' for e in r.evidence) or '- None'
    caps='\n'.join(f'- {c.name}: enabled={c.enabled} read_only={c.read_only} dry_run_only={c.dry_run_only}' for c in r.capabilities)
    routes='\n'.join(f'- {e.method} {e.path}' for e in r.route_index.endpoints)
    forbidden='\n'.join(f'- {e.method} {e.path}: forbidden route' for e in r.route_index.forbidden_routes)
    return f'''# Stage61 API Gateway Base Layer

## Decision
{r.decision.value}

## Safety Note
{r.safety_note}

## Evidence Summary
{ev}

## API Capability
{caps}

## Route Index
{routes}

## Safety Boundary
{_bul(r.safety_boundary.items)}

## Stage Status
- {r.stage_status.current_stage}: {r.stage_status.stage_name}

## Stage60 Pre-gray Final Review Evidence
- Read-only package evidence is summarized if available.

## Stage59 Read-only Seal Evidence
- Read-only package evidence is summarized if available.

## Stage58 Final Approval Evidence
- Read-only package evidence is summarized if available.

## Stage57 Gray Candidate Evidence
- Read-only package evidence is summarized if available.

## Stage56 Real Cache Quality Evidence
- Read-only package evidence is summarized if available.

## Stage55 QMT Dry-run Calibration Evidence
- Read-only package evidence is summarized if available.

## Roadmap Stage Plan Evidence
- 完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
- Stage61-75 UI 产品化路线继续保留；UI 不能绕过 Risk Gate / Human Approval / 不能直接访问 QMT / 不能自动 approve。

## Forbidden Routes
{forbidden}

## Required Manual Confirmations
- 人工复核 API Gateway 基础层材料。
- 确认 READY_FOR_API_GATEWAY_REVIEW 不是实盘授权。

## Blocking Reasons
{_bul(r.blocking_reasons)}

## Warnings
{_bul(r.warnings)}

## Next Stage Preview
Stage62 进入本地控制台报告读取层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
'''
