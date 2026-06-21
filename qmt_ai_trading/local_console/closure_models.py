from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleClosureDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW='READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW'
class LocalConsoleClosureStatus(str, Enum): PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleClosureSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleClosureFeatureType(str, Enum):
    STAGE_OVERVIEW='STAGE_OVERVIEW'; CAPABILITY_MATRIX='CAPABILITY_MATRIX'; SAFETY_BOUNDARY_TABLE='SAFETY_BOUNDARY_TABLE'; READONLY_DEMO_ENTRY='READONLY_DEMO_ENTRY'; ROUTE_COVERAGE_SUMMARY='ROUTE_COVERAGE_SUMMARY'; ASSET_COVERAGE_SUMMARY='ASSET_COVERAGE_SUMMARY'; RISK_LIMITATION_SUMMARY='RISK_LIMITATION_SUMMARY'; FINAL_ACCEPTANCE_DRAFT='FINAL_ACCEPTANCE_DRAFT'; FUTURE_ROADMAP_RECOMMENDATION='FUTURE_ROADMAP_RECOMMENDATION'; CLOSURE_REPORT='CLOSURE_REPORT'

@dataclass
class LocalConsoleClosureConfig:
    repo_root: str='.'; output_dir: str='local_console_closure_stage75'; demo_dir: str='local_console_demo_stage74'; help_dir: str='local_console_help_stage73'; acceptance_dir: str='local_console_acceptance_stage72'; review_dir: str='local_console_review_stage71'; drilldown_dir: str='local_console_drilldown_stage70'; grouping_dir: str='local_console_grouping_stage69'; refresh_dir: str='local_console_refresh_stage68'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleClosureEvidence:
    stage: str='Stage74'; path: str=''; status: LocalConsoleClosureStatus=LocalConsoleClosureStatus.UNAVAILABLE; decision: str=''; critical_count: int=0; summary: str=''; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class UiStageOverviewItem: stage: str='Stage75'; title: str='UI 产品化收口层'; status: LocalConsoleClosureStatus=LocalConsoleClosureStatus.PASS; note: str='本地只读 UI 产品化收口材料。'
@dataclass
class UiCapabilityMatrixItem: capability: str='UI 产品化阶段总览'; feature_type: LocalConsoleClosureFeatureType=LocalConsoleClosureFeatureType.STAGE_OVERVIEW; read_only: bool=True; safety_note: str='只读展示，不是审批授权，不是交易授权。'
@dataclass
class SafetyBoundaryTableItem: boundary: str='不调用 xttrader'; severity: LocalConsoleClosureSeverity=LocalConsoleClosureSeverity.INFO; status: LocalConsoleClosureStatus=LocalConsoleClosureStatus.PASS; note: str='安全横幅声明，不是可执行调用。'
@dataclass
class ReadonlyDemoEntryItem: entry: str='#/demo'; source: str='Stage74 demo package'; read_only: bool=True; note: str='只读演示入口。'
@dataclass
class UiRouteCoverageSummaryItem: route: str='#/closure'; allowed: bool=True; panel: str='closure-home-panel'; note: str='只读路由。'
@dataclass
class UiAssetCoverageSummaryItem: file_name: str='index.html'; asset_type: str='html'; read_only: bool=True; note: str='静态只读资产。'
@dataclass
class RiskLimitationSummaryItem: risk: str='不是实盘授权'; limitation: str='不下单、不查账户、不发送真实通知。'; mitigation: str='Stage76 先做路线重审。'
@dataclass
class FinalAcceptanceConclusionDraft: title: str='最终验收结论草稿'; conclusion: str='READY_FOR_UI_PRODUCTIZATION_CLOSURE_REVIEW 只表示 UI 产品化收口层材料可供人工复核，不是审批授权，不是交易授权。'; read_only: bool=True
@dataclass
class FutureRoadmapRecommendationItem: stage: str='Stage76'; recommendation: str='路线重审与下一轮开发计划层，不越级接实盘，需人工确认后再决定后续路线。'; read_only: bool=True
@dataclass
class UiProductizationClosureSafetyFinding: marker: str=''; path: str=''; severity: LocalConsoleClosureSeverity=LocalConsoleClosureSeverity.INFO; context: str=''; note: str=''
@dataclass
class UiStageOverviewReport: items: list[UiStageOverviewItem]=field(default_factory=list)
@dataclass
class UiCapabilityMatrixReport: items: list[UiCapabilityMatrixItem]=field(default_factory=list)
@dataclass
class SafetyBoundaryTableReport: items: list[SafetyBoundaryTableItem]=field(default_factory=list)
@dataclass
class ReadonlyDemoEntryReport: items: list[ReadonlyDemoEntryItem]=field(default_factory=list)
@dataclass
class UiRouteCoverageSummaryReport: items: list[UiRouteCoverageSummaryItem]=field(default_factory=list); forbidden_routes: list[str]=field(default_factory=list)
@dataclass
class UiAssetCoverageSummaryReport: items: list[UiAssetCoverageSummaryItem]=field(default_factory=list)
@dataclass
class RiskLimitationSummaryReport: items: list[RiskLimitationSummaryItem]=field(default_factory=list)
@dataclass
class FinalAcceptanceConclusionDraftReport: draft: FinalAcceptanceConclusionDraft=field(default_factory=FinalAcceptanceConclusionDraft)
@dataclass
class FutureRoadmapRecommendationReport: items: list[FutureRoadmapRecommendationItem]=field(default_factory=list)
@dataclass
class ClosureSafetyReport: findings: list[UiProductizationClosureSafetyFinding]=field(default_factory=list); critical_count: int=0; warnings: list[str]=field(default_factory=list)
@dataclass
class UiProductizationClosureReport:
    decision: LocalConsoleClosureDecision=LocalConsoleClosureDecision.NEED_MORE_EVIDENCE; config: LocalConsoleClosureConfig=field(default_factory=LocalConsoleClosureConfig); evidence: list[LocalConsoleClosureEvidence]=field(default_factory=list); stage_overview: list[UiStageOverviewItem]=field(default_factory=list); capability_matrix: list[UiCapabilityMatrixItem]=field(default_factory=list); safety_boundary_table: list[SafetyBoundaryTableItem]=field(default_factory=list); readonly_demo_entry: list[ReadonlyDemoEntryItem]=field(default_factory=list); route_coverage_summary: list[UiRouteCoverageSummaryItem]=field(default_factory=list); asset_coverage_summary: list[UiAssetCoverageSummaryItem]=field(default_factory=list); risk_limitation_summary: list[RiskLimitationSummaryItem]=field(default_factory=list); final_acceptance_conclusion_draft: FinalAcceptanceConclusionDraft=field(default_factory=FinalAcceptanceConclusionDraft); future_roadmap_recommendation: list[FutureRoadmapRecommendationItem]=field(default_factory=list); closure_safety_findings: list[UiProductizationClosureSafetyFinding]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':0})

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
