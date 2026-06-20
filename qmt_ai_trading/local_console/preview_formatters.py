from __future__ import annotations
import json
from .preview_models import *
def _bul(xs): return '\n'.join(f'- {x}' for x in xs) if xs else '- None'
def format_json_md(title,obj): return f'# {title}\n\n```json\n{obj}\n```\n'
def format_preview_report_md(r: PreviewServerReport):
    ev=_bul([f'{e.stage}: {e.status.value} decision={e.decision} critical={e.critical_count} path={e.path} encoding_warning={e.encoding_warning} summary={e.summary}' for e in r.evidence])
    return f'''# Stage67 Local Read-only Preview Server Layer

## Decision
{r.decision.value}

## Safety Note
本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。
READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW 只表示本地只读预览服务层材料可供人工复核。

## Evidence Summary
{ev}

## Preview Server Capability
- localhost static preview
- read_only=True
- dry_run_only=True
- no_trade_authorization=True

## Host / Port Boundary
- host={r.config.host}
- port={r.config.port}
- only_bind_127_0_0_1=True

## Allowed Preview Routes
{_bul([x.path for x in r.routes if x.allowed])}

## Forbidden Preview Routes
{_bul(['/order','/orders','/trade','/execute','/approve','/live','/notify','/account','/positions','/assets'])}

## Forbidden Preview Methods
- POST
- PUT
- PATCH
- DELETE

## Static File Index
{_bul([f'{f.path} exists={f.exists} size={f.size} encoding_warning={f.encoding_warning}' for f in r.static_files])}

## Response Manifest
{_bul([f'{m.route} -> {m.source_file} methods={m.methods}' for m in r.response_manifest])}

## Preview Safety Boundary
- public_bind={r.safety_boundary.public_bind}
- critical_findings={len(r.safety_boundary.critical_findings)}

## Stage66 Binding Evidence
{next((e.summary for e in r.evidence if e.stage=='Stage66'),'UNAVAILABLE')}

## Stage65 Shell Evidence
Read from Stage66 package when available; otherwise NEED_MORE_EVIDENCE.

## Stage64 Dashboard Evidence
Read from Stage66 data bundle when available.

## Tolerant Reader / Encoding Summary
如果读取到明显 mojibake / 乱码：encoding_warning=True；展示“上游报告存在编码异常，已隐藏乱码正文”；不输出大段乱码；不作为 CRITICAL；不阻断只读预览服务。

## Public Bind Check
{ 'PASS' if not r.safety_boundary.public_bind else 'FAIL' }

## Method Safety Check
Only GET / HEAD are allowed.

## Forbidden Server Actions
No QMT, no account query, no order, no real notification, no auto approve.

## Roadmap Stage Plan Evidence
完整工程阶段计划与前端 UI 产品化路线（Stage 1-75）继续保留。

## UI Productization Plan Evidence
Stage61-75：API Gateway / 本地控制台 / UI 产品化路线；UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## Required Manual Confirmations
- 人工复核 Stage67 本地只读预览服务层材料。
- 确认 READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW 不是实盘授权。

## Blocking Reasons
{_bul(r.blocking_reasons)}

## Warnings
{_bul(r.warnings)}

## Next Stage Preview
Stage68 进入本地控制台刷新与导航增强层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
'''
