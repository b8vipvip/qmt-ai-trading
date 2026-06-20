from __future__ import annotations
from .dashboard_models import *
def _bul(xs): return '\n'.join(f'- {x}' for x in xs) if xs else '- None'
def _metrics(c): return _bul([f'{m.name}: {m.value}' for m in c.metrics])
def format_card_md(card): return f'## {card.title}\nstatus={card.status.value}; read_only={card.read_only}; dry_run_only={card.dry_run_only}; no_trade_authorization={card.no_trade_authorization}\n\n{_metrics(card)}\n\nWarnings:\n{_bul(card.warnings)}\n'
def format_dashboard_report_md(r):
    cards='\n'.join(format_card_md(c) for c in r.cards); routes=_bul(r.route_index); ev=_bul([f'{e.stage}: {e.status.value} decision={e.decision} critical={e.critical_count} path={e.path}' for e in r.evidence])
    get=lambda cid: next((format_card_md(c) for c in r.cards if c.card_id==cid),'- UNAVAILABLE')
    return f'''# Stage64 Local Console Overview Dashboard Layer

## Decision
{r.decision.value}

## Safety Note
{r.safety_note}

## Evidence Summary
{ev}

## Dashboard Capability
- read_only=True
- dry_run_only=True
- no_trade_authorization=True
- Stage64 only generates local console overview dashboard cards.

## Dashboard Route Index
{routes}

## Dashboard Card Index
{_bul([c.card_id for c in r.cards])}

## Stage Status Cards
{get('stage-status')}

## Latest Validation Card
{get('latest-validation')}

## Warning / Blocking Stats
{get('warning-blocking-stats')}

## Manifest / Hash Status
{get('manifest-hash')}

## Scheduler Preview Status
{get('scheduler-preview')}

## Safety Boundary Status
{get('safety-boundary')}

## API Capability Status
{get('api-capability')}

## Detail / Filter Status
{get('detail-filter')}

## Stage63 Local Console Detail Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage63'),'UNAVAILABLE')}

## Stage62 Local Console Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage62'),'UNAVAILABLE')}

## Stage61 API Gateway Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage61'),'UNAVAILABLE')}

## Roadmap Stage Plan Evidence
完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
Stage61-75：API Gateway / 本地控制台 / UI 产品化路线；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## Forbidden Dashboard Routes
/order /orders /trade /execute /approve /live /notify /account /positions /assets are forbidden.

## Required Manual Confirmations
- 人工复核 Stage64 本地控制台概览面板层材料。

## Blocking Reasons
{_bul(r.blocking_reasons)}

## Warnings
{_bul(r.warnings)}

## Next Stage Preview
Stage65 进入本地控制台 shell / 静态页面骨架层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
'''
def format_card_index_md(r): return '# Stage64 Dashboard Card Index\n\n'+_bul([f'{c.card_id}: {c.title}' for c in r.cards])+'\n\n## Routes\n'+_bul(r.routes)+'\n'
def format_stage_status_cards_md(r): return '# Stage64 Stage Status Cards\n\n'+'\n'.join(format_card_md(c) for c in r.cards)
def format_single_card_report_md(title, card): return f'# Stage64 {title}\n\n'+format_card_md(card)
def format_next_shell_plan_md(r): return f'# Stage65 Console Shell Plan\n\n## Safety Note\n{r.safety_note}\n\n## Routes\n{_bul(r.routes)}\n\n## Plan Items\n{_bul(r.items)}\n'
