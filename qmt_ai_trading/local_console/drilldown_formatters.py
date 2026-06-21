from __future__ import annotations
import json
from .drilldown_models import *

def format_json_md(title, body): return f"# {title}\n\n```json\n{body}\n```\n"

def format_local_console_drilldown_report_md(r: LocalConsoleDrilldownReport) -> str:
    return f"""# Stage70 Local Console Report Drilldown and Export Layer

## Decision
{r.decision.value if hasattr(r.decision,'value') else r.decision}

## Safety Note
本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。
READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW 只表示本地控制台报告详情钻取与导出层材料可供人工复核。

## Evidence Summary
{json.dumps(to_plain(r.evidence), ensure_ascii=False, indent=2)}

## Drilldown Capability
报告详情钻取、单报告预览、复制摘要、导出本地 Markdown/JSON 快照、错误报告定位、人工复核包入口均为只读。

## Report Detail Index
{json.dumps(to_plain(r.detail_items), ensure_ascii=False, indent=2)}

## Single Report Preview
单报告预览只读取本地 report_detail_index，不查询账户、不请求交易接口。

## Copy Summary
copySummaryReadOnly 只复制摘要文本，不发送网络请求。

## Export Markdown Snapshot
导出 Markdown 仅为本地复核快照。

## Export JSON Snapshot
导出 JSON 包含 read_only=True / dry_run_only=True / no_trade_authorization=True。

## Export Manifest
{json.dumps(to_plain(r.export_manifest), ensure_ascii=False, indent=2)}

## Export Safety Report
{json.dumps(to_plain(r.safety_findings), ensure_ascii=False, indent=2)}

## Error Report Locator
错误报告定位仅返回本地 source_path。

## Manual Review Package Entry
Stage71 人工复核包入口为只读入口，不自动 approve。

## Forbidden Hash Routes
#/order #/orders #/trade #/execute #/approve #/live #/notify #/account #/positions #/assets 均显示只读错误占位。

## Forbidden JS Actions
未提供交易/账户/审批/通知 action。

## Stage69 Grouping Evidence
读取 Stage69 grouping report；若缺失则 NEED_MORE_EVIDENCE。

## Stage68 Refresh Evidence
读取 Stage68 refresh report 作为历史证据。

## Stage67 Preview Evidence
读取 Stage67 preview report 作为历史证据。

## Stage66 Binding Evidence
读取 Stage66 binding data bundle 作为历史证据。

## Roadmap Stage Plan Evidence
Stage70 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。

## UI Productization Plan Evidence
UI 不能绕过 Risk Gate / Human Approval，不能直接访问 QMT，不能自动 approve。

## Required Manual Confirmations
人工确认 Stage70 不是实盘授权。

## Blocking Reasons
{json.dumps(r.blocking_reasons, ensure_ascii=False, indent=2)}

## Warnings
{json.dumps(r.warnings, ensure_ascii=False, indent=2)}

## Next Stage Preview
Stage71 进入本地控制台人工复核工作台层；仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。
"""
