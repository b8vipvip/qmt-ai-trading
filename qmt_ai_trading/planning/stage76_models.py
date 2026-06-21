from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class Stage76RoadmapReviewDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_NEXT_ROADMAP_REVIEW='READY_FOR_NEXT_ROADMAP_REVIEW'
class Stage76ReviewStatus(str, Enum): PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class Stage76ReviewSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class Stage76ReviewArea(str, Enum):
    COMPLETED_STAGE_SUMMARY='COMPLETED_STAGE_SUMMARY'; UI_PRODUCTIZATION_RECAP='UI_PRODUCTIZATION_RECAP'; ARCHITECTURE_ALIGNMENT='ARCHITECTURE_ALIGNMENT'; SAFETY_BOUNDARY_RECAP='SAFETY_BOUNDARY_RECAP'; DATA_QUALITY_GAP='DATA_QUALITY_GAP'; TRADING_READINESS_GAP='TRADING_READINESS_GAP'; UI_MATURITY='UI_MATURITY'; LIVE_READINESS_BLOCKERS='LIVE_READINESS_BLOCKERS'; NEXT_ROADMAP='NEXT_ROADMAP'; STAGE77_PLAN='STAGE77_PLAN'

@dataclass
class Stage76RoadmapReviewConfig:
    repo_root: str='.'; output_dir: str='stage76_roadmap_review'; closure_dir: str='local_console_closure_stage75'; demo_dir: str='local_console_demo_stage74'; help_dir: str='local_console_help_stage73'; acceptance_dir: str='local_console_acceptance_stage72'; review_dir: str='local_console_review_stage71'; read_only: bool=True; no_trade_authorization: bool=True
@dataclass
class Stage76Evidence:
    stage: str='Stage75'; path: str=''; status: Stage76ReviewStatus=Stage76ReviewStatus.UNAVAILABLE; decision: str=''; critical_count: int=0; summary: str=''; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class CompletedStageSummaryItem: stage_range: str='Stage1-75'; status: Stage76ReviewStatus=Stage76ReviewStatus.PASS; summary: str='已完成安全基线、数据缓存、研究、风控、报告、调度、人工审批、API Gateway、本地控制台与 UI 产品化收口。'
@dataclass
class UiProductizationRecapItem: stage_range: str='Stage61-75'; status: Stage76ReviewStatus=Stage76ReviewStatus.PASS; summary: str='API Gateway / 本地控制台 / UI 产品化路线已收口，但不是实盘授权。'
@dataclass
class ArchitectureAlignmentItem: area: str='总体架构'; status: Stage76ReviewStatus=Stage76ReviewStatus.PASS; note: str='路线仍保持 AI/Research 只生成建议，Risk Gate 与 Human Approval 位于执行边界前。'
@dataclass
class SafetyBoundaryRecapItem: boundary: str='不调用 xttrader'; severity: Stage76ReviewSeverity=Stage76ReviewSeverity.INFO; status: Stage76ReviewStatus=Stage76ReviewStatus.PASS; note: str='Stage76 只读规划，不执行交易、账户查询、真实通知或自动 approve。'
@dataclass
class DataQualityGapItem: gap: str='没有完成真实缓存长期质量验证'; severity: Stage76ReviewSeverity=Stage76ReviewSeverity.WARN; recommendation: str='Stage77/78 继续复核真实缓存覆盖率、稳定性和质量报告。'
@dataclass
class TradingReadinessGapItem: gap: str='Paper Trading 长周期复盘不足'; severity: Stage76ReviewSeverity=Stage76ReviewSeverity.WARN; recommendation: str='Stage79 做长周期复盘与归因，不直接实盘。'
@dataclass
class UiMaturityItem: capability: str='本地控制台只读复核'; status: Stage76ReviewStatus=Stage76ReviewStatus.PASS; note: str='UI 可用于人工复核，但不能绕过 Risk Gate / Human Approval，不能直接访问 QMT。'
@dataclass
class LiveReadinessBlocker: blocker: str='UI 完成不等于交易链路成熟'; severity: Stage76ReviewSeverity=Stage76ReviewSeverity.CRITICAL; note: str='阻断实盘，需后续阶段逐步验证。'
@dataclass
class NextRoadmapStageItem: stage: str='Stage77'; title: str='实盘前安全审计重启与真实数据质量复核层'; priority: str='P0'; note: str='仍不直接实盘，只做审计与复核。'
@dataclass
class NextPriorityMatrixItem: item: str='安全审计重启'; priority: str='P0'; rationale: str='未完成前不得进入实盘。'
@dataclass
class Stage77PlanItem: task: str='重启实盘前安全审计'; priority: str='P0'; note: str='不调用 xttrader，不查询真实账户，不下单。'
@dataclass
class Stage76ArchitectureReviewReport: items: list[ArchitectureAlignmentItem]=field(default_factory=list)
@dataclass
class Stage76SafetyBoundaryReviewReport: items: list[SafetyBoundaryRecapItem]=field(default_factory=list)
@dataclass
class Stage76DataQualityGapReport: items: list[DataQualityGapItem]=field(default_factory=list)
@dataclass
class Stage76TradingReadinessGapReport: items: list[TradingReadinessGapItem]=field(default_factory=list)
@dataclass
class Stage76UiMaturityReport: items: list[UiMaturityItem]=field(default_factory=list)
@dataclass
class Stage76NextRoadmapPlanReport: stages: list[NextRoadmapStageItem]=field(default_factory=list); priorities: list[NextPriorityMatrixItem]=field(default_factory=list)
@dataclass
class Stage76RoadmapReviewReport:
    decision: Stage76RoadmapReviewDecision=Stage76RoadmapReviewDecision.NEED_MORE_EVIDENCE; config: Stage76RoadmapReviewConfig=field(default_factory=Stage76RoadmapReviewConfig); evidence: list[Stage76Evidence]=field(default_factory=list); completed_stage_summary: list[CompletedStageSummaryItem]=field(default_factory=list); ui_productization_recap: list[UiProductizationRecapItem]=field(default_factory=list); architecture_alignment: list[ArchitectureAlignmentItem]=field(default_factory=list); safety_boundary: list[SafetyBoundaryRecapItem]=field(default_factory=list); data_quality_gaps: list[DataQualityGapItem]=field(default_factory=list); trading_readiness_gaps: list[TradingReadinessGapItem]=field(default_factory=list); ui_maturity: list[UiMaturityItem]=field(default_factory=list); live_readiness_blockers: list[LiveReadinessBlocker]=field(default_factory=list); next_roadmap: list[NextRoadmapStageItem]=field(default_factory=list); priority_matrix: list[NextPriorityMatrixItem]=field(default_factory=list); stage77_plan: list[Stage77PlanItem]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); safety_note: str='本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_NEXT_ROADMAP_REVIEW 只表示路线重审材料可供人工复核。Stage75 UI 产品化收口不等于实盘授权。'; summary: dict[str,Any]=field(default_factory=lambda:{'critical_count':0,'read_only':True,'no_trade_authorization':True})

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
