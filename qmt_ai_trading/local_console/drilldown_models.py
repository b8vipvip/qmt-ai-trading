from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleDrilldownDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW='READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW'
class LocalConsoleDrilldownStatus(str, Enum): PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleDrilldownSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleDrilldownFeatureType(str, Enum):
    REPORT_DRILLDOWN='REPORT_DRILLDOWN'; SINGLE_REPORT_PREVIEW='SINGLE_REPORT_PREVIEW'; COPY_SUMMARY='COPY_SUMMARY'; EXPORT_MARKDOWN_SNAPSHOT='EXPORT_MARKDOWN_SNAPSHOT'; EXPORT_JSON_SNAPSHOT='EXPORT_JSON_SNAPSHOT'; ERROR_REPORT_LOCATOR='ERROR_REPORT_LOCATOR'; REVIEW_PACKAGE_ENTRY='REVIEW_PACKAGE_ENTRY'; EXPORT_SAFETY='EXPORT_SAFETY'; NEXT_STAGE_PLAN='NEXT_STAGE_PLAN'

@dataclass
class LocalConsoleDrilldownConfig:
    repo_root: str='.'; output_dir: str='local_console_drilldown_stage70'; binding_dir: str='local_console_binding_stage66'; grouping_dir: str='local_console_grouping_stage69'; refresh_dir: str='local_console_refresh_stage68'; preview_dir: str='local_console_preview_stage67'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleDrilldownEvidence:
    stage: str='Stage69'; path: str=''; status: LocalConsoleDrilldownStatus=LocalConsoleDrilldownStatus.UNAVAILABLE; decision: str=''; critical_count: int=0; summary: str=''; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class ReportDetailItem:
    report_id: str='stage70-overview'; title: str='Stage70 Overview'; source_path: str='local_console_drilldown_report.md'; status: str='PASS'; severity: str='INFO'; stage: str='Stage70'; summary: str='本地只读控制台报告详情钻取与导出层'; tags: list[str]=field(default_factory=lambda:['read_only','stage70'])
@dataclass
class ReportDrilldownRoute:
    route: str='#/reports/detail'; title: str='Report Detail'; read_only: bool=True; forbidden: bool=False
@dataclass
class ReportPreviewModel:
    report_id: str='stage70-overview'; preview_markdown: str='只读预览，不是实盘授权。'; read_only: bool=True
@dataclass
class CopySummaryAction:
    action_id: str='copySummaryButton'; report_id: str='stage70-overview'; read_only: bool=True; network_enabled: bool=False
@dataclass
class ExportSnapshot:
    snapshot_id: str='stage70-readonly-snapshot'; report_id: str='stage70-overview'; markdown_filename: str='export_snapshot.md'; json_filename: str='export_snapshot.json'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; note: str='导出仅为本地 Markdown/JSON 复核快照，不是交易授权。'; payload: dict[str,Any]=field(default_factory=dict)
@dataclass
class ExportManifest:
    stage: str='Stage70'; allowed_formats: list[str]=field(default_factory=lambda:['markdown','json']); output_dir: str='local_console_drilldown_stage70'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; sources: list[str]=field(default_factory=lambda:['local_console_drilldown_report.md','report_detail_index.md','drilldown_route_map.md'])
@dataclass
class ExportSafetyFinding:
    marker: str=''; path: str=''; severity: LocalConsoleDrilldownSeverity=LocalConsoleDrilldownSeverity.INFO; context: str=''; note: str=''
@dataclass
class ReviewPackageEntry:
    route: str='#/review-package'; title: str='Manual Review Package Entry'; read_only: bool=True; next_stage: str='Stage71'
@dataclass
class LocalConsoleDrilldownReport:
    decision: LocalConsoleDrilldownDecision=LocalConsoleDrilldownDecision.NEED_MORE_EVIDENCE; config: LocalConsoleDrilldownConfig=field(default_factory=LocalConsoleDrilldownConfig); evidence: list[LocalConsoleDrilldownEvidence]=field(default_factory=list); detail_items: list[ReportDetailItem]=field(default_factory=list); routes: list[ReportDrilldownRoute]=field(default_factory=list); export_manifest: ExportManifest=field(default_factory=ExportManifest); export_snapshot: ExportSnapshot=field(default_factory=ExportSnapshot); safety_findings: list[ExportSafetyFinding]=field(default_factory=list); review_entry: ReviewPackageEntry=field(default_factory=ReviewPackageEntry); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':0})
@dataclass
class ReportDetailIndexReport: items: list[ReportDetailItem]=field(default_factory=list)
@dataclass
class ReportDrilldownRouteMapReport: routes: list[ReportDrilldownRoute]=field(default_factory=list)
@dataclass
class ExportManifestReport: manifest: ExportManifest=field(default_factory=ExportManifest)
@dataclass
class ExportSnapshotReport: snapshot: ExportSnapshot=field(default_factory=ExportSnapshot)
@dataclass
class ExportSafetyReport: findings: list[ExportSafetyFinding]=field(default_factory=list); critical_count: int=0; warnings: list[str]=field(default_factory=list)
@dataclass
class NextManualReviewWorkbenchPlanReport:
    stage: str='Stage71'; title: str='本地控制台人工复核工作台层'; items: list[str]=field(default_factory=lambda:['人工复核工作台','复核清单','只读 review notes 模板','本地确认项列表','复核包目录索引','Stage72 UI 验收汇总层预告']); safety_note: str='Stage71 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
