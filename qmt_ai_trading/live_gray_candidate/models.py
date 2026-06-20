from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LiveGrayCandidateDecision(str, Enum):
    NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_GRAY_CANDIDATE_REVIEW="READY_FOR_GRAY_CANDIDATE_REVIEW"
class LiveGrayCandidateStatus(str, Enum):
    PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"; UNAVAILABLE="UNAVAILABLE"
class LiveGrayCandidateSeverity(str, Enum):
    INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class LiveGrayCandidateCategory(str, Enum):
    STAGE56_REAL_CACHE_QUALITY="STAGE56_REAL_CACHE_QUALITY"; STAGE55_QMT_DRYRUN_CALIBRATION="STAGE55_QMT_DRYRUN_CALIBRATION"; GRAY_CAPITAL_LIMIT="GRAY_CAPITAL_LIMIT"; SINGLE_TRADE_LIMIT="SINGLE_TRADE_LIMIT"; DAILY_TRADE_LIMIT="DAILY_TRADE_LIMIT"; ETF_WHITELIST="ETF_WHITELIST"; POSITION_LIMIT="POSITION_LIMIT"; CASH_RESERVE="CASH_RESERVE"; DRAWDOWN_TRIGGER="DRAWDOWN_TRIGGER"; DAILY_LOSS_TRIGGER="DAILY_LOSS_TRIGGER"; DATA_QUALITY_BLOCKER="DATA_QUALITY_BLOCKER"; RISK_GATE="RISK_GATE"; HUMAN_APPROVAL="HUMAN_APPROVAL"; ROLLBACK_PLAN="ROLLBACK_PLAN"; CIRCUIT_BREAKER="CIRCUIT_BREAKER"; STOP_CONDITION="STOP_CONDITION"; REVIEW_REPORT="REVIEW_REPORT"; ROADMAP_STAGE_PLAN="ROADMAP_STAGE_PLAN"; UI_PRODUCTIZATION_PLAN="UI_PRODUCTIZATION_PLAN"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"

@dataclass
class LiveGrayCandidateConfig:
    repo_root: str|Path = "."; output_dir: str|Path = "live_gray_candidate_stage57"; real_cache_quality_dir: str|Path = "real_cache_quality_stage56"; qmt_dryrun_calibration_dir: str|Path = "qmt_dryrun_calibration_stage55"; roadmap_path: str = "docs/qmt-ai-trading-project-roadmap.md"; gray_total_capital_limit: float = 1000.0; single_trade_capital_limit: float = 200.0; daily_trade_capital_limit: float = 300.0; max_positions: int = 2; max_single_symbol_weight: float = 0.20; max_portfolio_exposure: float = 0.50; cash_reserve_ratio: float = 0.50; max_daily_loss_ratio: float = 0.01; max_total_drawdown_ratio: float = 0.03; max_orders_per_day: int = 2; cooldown_days_after_stop: int = 3; allowed_symbols_source: str = "default_etf universe / Stage56 validated symbols"
@dataclass
class LiveGrayCandidateEvidence:
    category: LiveGrayCandidateCategory = LiveGrayCandidateCategory.SYSTEM; status: LiveGrayCandidateStatus = LiveGrayCandidateStatus.SKIPPED; severity: LiveGrayCandidateSeverity = LiveGrayCandidateSeverity.INFO; title: str = ""; summary: str = ""; path: str = ""; metadata: dict[str, Any] = field(default_factory=dict)
@dataclass
class GrayCapitalLimitItem:
    name: str=""; value: str=""; status: LiveGrayCandidateStatus=LiveGrayCandidateStatus.PASS; summary: str=""
@dataclass
class GrayRiskLimitItem:
    name: str=""; limit: str=""; trigger: str=""; action: str="人工复核；不自动执行"
@dataclass
class GrayApprovalItem:
    name: str=""; required: bool=True; summary: str=""
@dataclass
class GrayRollbackItem:
    name: str=""; trigger: str=""; action: str="停止候选流程并人工复核"
@dataclass
class GrayStopConditionItem:
    name: str=""; threshold: str=""; action: str="停止灰度候选推进"
@dataclass
class NextApprovalPackagePlanItem:
    name: str=""; summary: str=""; safety_note: str="下一阶段仍不自动实盘。"
@dataclass
class LiveGrayCandidateReport:
    decision: LiveGrayCandidateDecision=LiveGrayCandidateDecision.NEED_MORE_EVIDENCE; safety_note: str="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_GRAY_CANDIDATE_REVIEW 只表示小资金灰度候选计划材料可供人工复核。"; evidence: list[LiveGrayCandidateEvidence]=field(default_factory=list); allowed_symbols: list[str]=field(default_factory=list); capital_limits: list[GrayCapitalLimitItem]=field(default_factory=list); risk_limits: list[GrayRiskLimitItem]=field(default_factory=list); approval_items: list[GrayApprovalItem]=field(default_factory=list); rollback_items: list[GrayRollbackItem]=field(default_factory=list); stop_conditions: list[GrayStopConditionItem]=field(default_factory=list); next_plan_items: list[NextApprovalPackagePlanItem]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); summary: dict[str, Any]=field(default_factory=dict)
@dataclass
class GrayRiskLimitReport: items: list[GrayRiskLimitItem]=field(default_factory=list); decision: LiveGrayCandidateDecision=LiveGrayCandidateDecision.NEED_MORE_EVIDENCE; safety_note: str="灰度风险限制只用于候选计划，不代表实盘授权。"
@dataclass
class GrayApprovalChecklistReport: items: list[GrayApprovalItem]=field(default_factory=list); decision: LiveGrayCandidateDecision=LiveGrayCandidateDecision.NEED_MORE_EVIDENCE; safety_note: str="人工审批清单不会自动 approve。"
@dataclass
class GrayRollbackCircuitBreakerReport: rollback_items: list[GrayRollbackItem]=field(default_factory=list); stop_conditions: list[GrayStopConditionItem]=field(default_factory=list); decision: LiveGrayCandidateDecision=LiveGrayCandidateDecision.NEED_MORE_EVIDENCE; safety_note: str="回滚与熔断计划只读生成，不执行交易。"
@dataclass
class NextApprovalPackagePlanReport: items: list[NextApprovalPackagePlanItem]=field(default_factory=list); decision: LiveGrayCandidateDecision=LiveGrayCandidateDecision.NEED_MORE_EVIDENCE; safety_note: str="Stage58 仍不得直接实盘。"

def to_plain(obj: Any) -> Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj, "__dataclass_fields__"): return {k: to_plain(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list): return [to_plain(x) for x in obj]
    if isinstance(obj, dict): return {k: to_plain(v) for k, v in obj.items()}
    if isinstance(obj, Path): return str(obj)
    return obj
