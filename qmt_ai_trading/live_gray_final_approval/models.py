from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LiveGrayFinalApprovalDecision(str, Enum):
    NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_FINAL_APPROVAL_REVIEW="READY_FOR_FINAL_APPROVAL_REVIEW"
class LiveGrayFinalApprovalStatus(str, Enum):
    PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"; UNAVAILABLE="UNAVAILABLE"
class LiveGrayFinalApprovalSeverity(str, Enum):
    INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveGrayFinalApprovalCategory(str, Enum):
    STAGE57_GRAY_CANDIDATE="STAGE57_GRAY_CANDIDATE"; STAGE56_REAL_CACHE_QUALITY="STAGE56_REAL_CACHE_QUALITY"; STAGE55_QMT_DRYRUN_CALIBRATION="STAGE55_QMT_DRYRUN_CALIBRATION"; CAPITAL_APPROVAL="CAPITAL_APPROVAL"; POSITION_APPROVAL="POSITION_APPROVAL"; ETF_WHITELIST_APPROVAL="ETF_WHITELIST_APPROVAL"; RISK_GATE_APPROVAL="RISK_GATE_APPROVAL"; HUMAN_APPROVAL_FLOW="HUMAN_APPROVAL_FLOW"; PAPER_TRADING_EVIDENCE="PAPER_TRADING_EVIDENCE"; ROLLBACK_APPROVAL="ROLLBACK_APPROVAL"; CIRCUIT_BREAKER_APPROVAL="CIRCUIT_BREAKER_APPROVAL"; LOG_REVIEW_REQUIREMENT="LOG_REVIEW_REQUIREMENT"; REVIEW_REPORT_REQUIREMENT="REVIEW_REPORT_REQUIREMENT"; FINAL_SIGNOFF="FINAL_SIGNOFF"; ROADMAP_STAGE_PLAN="ROADMAP_STAGE_PLAN"; UI_PRODUCTIZATION_PLAN="UI_PRODUCTIZATION_PLAN"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"

@dataclass
class LiveGrayFinalApprovalConfig:
    repo_root: str|Path="."; output_dir: str|Path="live_gray_final_approval_stage58"; live_gray_candidate_dir: str|Path="live_gray_candidate_stage57"; real_cache_quality_dir: str|Path="real_cache_quality_stage56"; qmt_dryrun_calibration_dir: str|Path="qmt_dryrun_calibration_stage55"; roadmap_path: str="docs/qmt-ai-trading-project-roadmap.md"
@dataclass
class LiveGrayFinalApprovalEvidence:
    category: LiveGrayFinalApprovalCategory=LiveGrayFinalApprovalCategory.SYSTEM; status: LiveGrayFinalApprovalStatus=LiveGrayFinalApprovalStatus.SKIPPED; severity: LiveGrayFinalApprovalSeverity=LiveGrayFinalApprovalSeverity.INFO; title: str=""; summary: str=""; path: str=""; metadata: dict[str, Any]=field(default_factory=dict)
@dataclass
class FinalApprovalChecklistItem:
    name: str=""; required: bool=True; status: LiveGrayFinalApprovalStatus=LiveGrayFinalApprovalStatus.WARN; summary: str="必须人工勾选确认；不代表实盘授权"
@dataclass
class CapitalPositionApprovalItem:
    name: str=""; value: str="待人工确认"; status: LiveGrayFinalApprovalStatus=LiveGrayFinalApprovalStatus.WARN; manual_signoff_status: str="PENDING_MANUAL_SIGNOFF"; summary: str="只读审批项，不代表实盘授权"
@dataclass
class RiskHumanApprovalItem:
    name: str=""; status: LiveGrayFinalApprovalStatus=LiveGrayFinalApprovalStatus.WARN; summary: str="必须人工复核；不可绕过"
@dataclass
class RollbackCircuitApprovalItem:
    name: str=""; trigger: str="待人工复核"; action: str="停止推进并人工复核；只读说明，不自动执行"
@dataclass
class FinalSignoffItem:
    role: str=""; required: bool=True; status: str="PENDING_MANUAL_SIGNOFF"; statement: str="未签字前不允许进入后续真实执行审批"
@dataclass
class NextReadOnlySealPlanItem:
    name: str=""; status: LiveGrayFinalApprovalStatus=LiveGrayFinalApprovalStatus.WARN; summary: str="Stage59 只读封版计划项；不自动实盘"
@dataclass
class LiveGrayFinalApprovalReport:
    decision: LiveGrayFinalApprovalDecision=LiveGrayFinalApprovalDecision.NEED_MORE_EVIDENCE
    safety_note: str="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_FINAL_APPROVAL_REVIEW 只表示小资金灰度前最终人工审批包材料可供人工复核。"
    evidence: list[LiveGrayFinalApprovalEvidence]=field(default_factory=list); checklist_items: list[FinalApprovalChecklistItem]=field(default_factory=list); capital_position_items: list[CapitalPositionApprovalItem]=field(default_factory=list); risk_human_items: list[RiskHumanApprovalItem]=field(default_factory=list); rollback_circuit_items: list[RollbackCircuitApprovalItem]=field(default_factory=list); signoff_items: list[FinalSignoffItem]=field(default_factory=list); next_seal_plan_items: list[NextReadOnlySealPlanItem]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); summary: dict[str, Any]=field(default_factory=dict)
@dataclass
class CapitalPositionApprovalReport: items: list[CapitalPositionApprovalItem]=field(default_factory=list); decision: LiveGrayFinalApprovalDecision=LiveGrayFinalApprovalDecision.NEED_MORE_EVIDENCE; safety_note: str="资金与仓位审批表只读生成，不代表实盘授权。"
@dataclass
class RiskHumanApprovalReviewReport: items: list[RiskHumanApprovalItem]=field(default_factory=list); decision: LiveGrayFinalApprovalDecision=LiveGrayFinalApprovalDecision.NEED_MORE_EVIDENCE; safety_note: str="Risk Gate / Human Approval 审批复核表不自动 approve。"
@dataclass
class RollbackCircuitApprovalReport: items: list[RollbackCircuitApprovalItem]=field(default_factory=list); decision: LiveGrayFinalApprovalDecision=LiveGrayFinalApprovalDecision.NEED_MORE_EVIDENCE; safety_note: str="回滚与熔断审批表只读生成，不执行交易。"
@dataclass
class FinalSignoffChecklistReport: items: list[FinalSignoffItem]=field(default_factory=list); decision: LiveGrayFinalApprovalDecision=LiveGrayFinalApprovalDecision.NEED_MORE_EVIDENCE; safety_note: str="最终签字清单必须人工签署；不代表实盘授权。"
@dataclass
class NextReadOnlySealPlanReport: items: list[NextReadOnlySealPlanItem]=field(default_factory=list); decision: LiveGrayFinalApprovalDecision=LiveGrayFinalApprovalDecision.NEED_MORE_EVIDENCE; safety_note: str="Stage59 仍不得直接实盘，只能只读封版。"

def to_plain(obj: Any) -> Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj, "__dataclass_fields__"): return {k: to_plain(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list): return [to_plain(x) for x in obj]
    if isinstance(obj, dict): return {k: to_plain(v) for k, v in obj.items()}
    if isinstance(obj, Path): return str(obj)
    return obj
