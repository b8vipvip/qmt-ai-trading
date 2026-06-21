from __future__ import annotations
import json
from .grouping_models import *

def format_json_md(title, payload): return f"# {title}\n\n```json\n{payload}\n```\n"

def format_local_console_grouping_report_md(r: LocalConsoleGroupingReport)->str:
    lines=['# Stage69 Local Console Grouping and Filtering Experience Layer','','## Decision',r.decision.value,'','## Safety Note','本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。','READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW 只表示本地控制台状态分组与筛选体验层材料可供人工复核。','']
    for h in ['Evidence Summary','Grouping Capability','Filter Bar','Status Grouping','Severity Grouping','Stage Grouping','Warning Filter','Blocking Reason Filter','Read-only Search','Collapse / Expand','Count Badges','Empty State','Frontend Grouping Safety Report','Forbidden Hash Routes','Forbidden JS Actions','Stage68 Refresh Evidence','Stage67 Preview Evidence','Stage66 Binding Evidence','Roadmap Stage Plan Evidence','UI Productization Plan Evidence','Required Manual Confirmations','Blocking Reasons','Warnings']:
        lines += [f'## {h}', json.dumps(to_plain(r.summary if h.endswith('Summary') else {'warnings':r.warnings,'blocking_reasons':r.blocking_reasons}), ensure_ascii=False, indent=2), '']
    lines += ['## Next Stage Preview','Stage70 进入本地控制台报告详情钻取与导出层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。','']
    return '\n'.join(lines)
