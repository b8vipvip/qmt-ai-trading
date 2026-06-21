from __future__ import annotations
import json
from .stage76_models import *

def json_md(title: str, obj) -> str:
    return f'# {title}\n\n```json\n{json.dumps(to_plain(obj), ensure_ascii=False, indent=2)}\n```\n'

def bullets(items, attr='summary'):
    return '\n'.join(f'- {getattr(x, attr, str(x))}' for x in items) or '- 暂无。'

def format_stage76_report_md(r: Stage76RoadmapReviewReport) -> str:
    return f'''# Stage76 Roadmap Review and Next Development Plan

## Decision
{r.decision.value}

## Safety Note
{r.safety_note}

## Evidence Summary
{bullets(r.evidence, 'summary')}

## Completed Stage Summary
Stage1-75 已完成成果总览。
{bullets(r.completed_stage_summary)}

## UI Productization Recap
Stage61-75 UI 产品化路线复盘。
{bullets(r.ui_productization_recap)}

## Architecture Alignment Review
架构与 roadmap 是否一致。
{bullets(r.architecture_alignment, 'note')}

## Safety Boundary Review
当前安全边界复盘。
{bullets(r.safety_boundary, 'note')}

## Data Quality Gap Review
真实缓存、数据覆盖率、质量报告、mock fallback 使用限制。
{bullets(r.data_quality_gaps, 'gap')}

## Trading Readiness Gap Review
实盘前仍缺哪些条件。
{bullets(r.trading_readiness_gaps, 'gap')}

## UI Maturity Review
本地控制台成熟度、只读边界、可复核性。
{bullets(r.ui_maturity, 'note')}

## Live Readiness Blockers
列出阻断实盘的关键条件。
{bullets(r.live_readiness_blockers, 'blocker')}

## Next Roadmap Plan
下一轮阶段建议。
{bullets(r.next_roadmap, 'note')}

## Stage77 Plan
建议 Stage77 做什么。
{bullets(r.stage77_plan, 'note')}

## Required Manual Confirmations
- 人工确认 Stage76 只读规划材料。
- 人工确认 READY_FOR_NEXT_ROADMAP_REVIEW 不是实盘授权。

## Blocking Reasons
{chr(10).join('- '+x for x in r.blocking_reasons) or '- 当前报告级阻断项见实盘前阻断清单。'}

## Warnings
{chr(10).join('- '+x for x in r.warnings) or '- 无额外警告。'}

## Encoding / UTF-8 Check
- Python/Markdown/JSON 使用 UTF-8，JSON ensure_ascii=False，不输出 NUL、BOM 乱码或明显 mojibake。

## Next Stage Preview
Stage77 建议进入“实盘前安全审计重启与真实数据质量复核层”，但仍不直接实盘。
'''
