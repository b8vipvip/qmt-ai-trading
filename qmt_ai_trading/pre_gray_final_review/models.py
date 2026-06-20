from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class PreGrayFinalReviewDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_PRE_GRAY_FINAL_REVIEW='READY_FOR_PRE_GRAY_FINAL_REVIEW'
class GoNoGoDraftDecision(str, Enum):
    GO_DRAFT='GO_DRAFT'; NO_GO_DRAFT='NO_GO_DRAFT'; NEED_MORE_EVIDENCE_DRAFT='NEED_MORE_EVIDENCE_DRAFT'
class PreGrayFinalReviewStatus(str, Enum):
    PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class PreGrayFinalReviewSeverity(str, Enum):
    INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class PreGrayFinalReviewCategory(str, Enum):
    STAGE59_READONLY_SEAL='STAGE59_READONLY_SEAL'; STAGE58_FINAL_APPROVAL='STAGE58_FINAL_APPROVAL'; STAGE57_GRAY_CANDIDATE='STAGE57_GRAY_CANDIDATE'; STAGE56_REAL_CACHE_QUALITY='STAGE56_REAL_CACHE_QUALITY'; STAGE55_QMT_DRYRUN_CALIBRATION='STAGE55_QMT_DRYRUN_CALIBRATION'; MATERIAL_RECHECK='MATERIAL_RECHECK'; PRE_RUN_CHECKLIST_RECHECK='PRE_RUN_CHECKLIST_RECHECK'; MANIFEST_HASH_RECHECK='MANIFEST_HASH_RECHECK'; RISK_GATE_FINAL_RECHECK='RISK_GATE_FINAL_RECHECK'; HUMAN_APPROVAL_FINAL_RECHECK='HUMAN_APPROVAL_FINAL_RECHECK'; PAPER_DRY_RUN_EVIDENCE='PAPER_DRY_RUN_EVIDENCE'; REGISTER_PREVIEW_RECHECK='REGISTER_PREVIEW_RECHECK'; GO_CONDITION='GO_CONDITION'; NO_GO_BLOCKER='NO_GO_BLOCKER'; GO_NO_GO_DRAFT='GO_NO_GO_DRAFT'; STAGE61_API_GATEWAY_PLAN='STAGE61_API_GATEWAY_PLAN'; ROADMAP_STAGE_PLAN='ROADMAP_STAGE_PLAN'; UI_PRODUCTIZATION_PLAN='UI_PRODUCTIZATION_PLAN'; QMT_BOUNDARY='QMT_BOUNDARY'; SCHEDULER_PREVIEW='SCHEDULER_PREVIEW'; NOTIFICATION_DRY_RUN='NOTIFICATION_DRY_RUN'; RUNTIME_ARTIFACT='RUNTIME_ARTIFACT'; SENSITIVE_FILE='SENSITIVE_FILE'; SYSTEM='SYSTEM'

@dataclass
class PreGrayFinalReviewConfig:
    repo_root: str|Path='.'; output_dir: str|Path='pre_gray_final_review_stage60'; live_gray_readonly_seal_dir: str|Path='live_gray_readonly_seal_stage59'; live_gray_final_approval_dir: str|Path='live_gray_final_approval_stage58'; live_gray_candidate_dir: str|Path='live_gray_candidate_stage57'; real_cache_quality_dir: str|Path='real_cache_quality_stage56'; qmt_dryrun_calibration_dir: str|Path='qmt_dryrun_calibration_stage55'; roadmap_path: str='docs/qmt-ai-trading-project-roadmap.md'
@dataclass
class PreGrayFinalReviewEvidence:
    category: PreGrayFinalReviewCategory=PreGrayFinalReviewCategory.SYSTEM; status: PreGrayFinalReviewStatus=PreGrayFinalReviewStatus.SKIPPED; severity: PreGrayFinalReviewSeverity=PreGrayFinalReviewSeverity.INFO; title: str=''; summary: str=''; path: str=''; metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class MaterialRecheckItem: name: str=''; status: PreGrayFinalReviewStatus=PreGrayFinalReviewStatus.WARN; summary: str='只读复核材料，待人工确认；不代表实盘授权'
@dataclass
class PreRunChecklistRecheckItem: name: str=''; status: PreGrayFinalReviewStatus=PreGrayFinalReviewStatus.WARN; summary: str='运行前 checklist 复核；仍不实盘'
@dataclass
class ManifestHashRecheckItem: name: str=''; exists: bool=False; sha256_present: bool=False; status: PreGrayFinalReviewStatus=PreGrayFinalReviewStatus.WARN; summary: str='manifest/hash 只读复核'
@dataclass
class RiskHumanFinalRecheckItem: name: str=''; status: PreGrayFinalReviewStatus=PreGrayFinalReviewStatus.WARN; summary: str='Risk Gate / Human Approval 不可绕过'
@dataclass
class PaperDryRunEvidenceItem: name: str=''; status: PreGrayFinalReviewStatus=PreGrayFinalReviewStatus.WARN; summary: str='Paper Trading / dry-run 证据只读复核'
@dataclass
class GoConditionItem: name: str=''; satisfied: bool=False; summary: str='GO 条件草案；不代表实盘授权'
@dataclass
class NoGoBlockerItem: name: str=''; active: bool=False; severity: PreGrayFinalReviewSeverity=PreGrayFinalReviewSeverity.WARN; summary: str='NO-GO 阻断条件草案'
@dataclass
class GoNoGoDraftItem: name: str=''; status: PreGrayFinalReviewStatus=PreGrayFinalReviewStatus.WARN; summary: str='go/no-go 草案项；不代表实盘授权'
@dataclass
class Stage61ApiGatewayPlanItem: name: str=''; status: PreGrayFinalReviewStatus=PreGrayFinalReviewStatus.PASS; summary: str='Stage61 API Gateway 基础层；只读 API 边界，不接实盘'
@dataclass
class PreGrayFinalReviewReport:
    decision: PreGrayFinalReviewDecision=PreGrayFinalReviewDecision.NEED_MORE_EVIDENCE
    go_no_go_decision: GoNoGoDraftDecision=GoNoGoDraftDecision.NEED_MORE_EVIDENCE_DRAFT
    safety_note: str='本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_PRE_GRAY_FINAL_REVIEW 只表示预灰度最终复核与 go/no-go 材料可供人工复核。GO_DRAFT 不是实盘授权。'
    evidence: list[PreGrayFinalReviewEvidence]=field(default_factory=list); material_items: list[MaterialRecheckItem]=field(default_factory=list); checklist_items: list[PreRunChecklistRecheckItem]=field(default_factory=list); manifest_items: list[ManifestHashRecheckItem]=field(default_factory=list); risk_human_items: list[RiskHumanFinalRecheckItem]=field(default_factory=list); paper_items: list[PaperDryRunEvidenceItem]=field(default_factory=list); blockers: list[NoGoBlockerItem]=field(default_factory=list); conditions: list[GoConditionItem]=field(default_factory=list); gonogo_items: list[GoNoGoDraftItem]=field(default_factory=list); stage61_items: list[Stage61ApiGatewayPlanItem]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=dict)
@dataclass
class MaterialRecheckReport: items: list[MaterialRecheckItem]=field(default_factory=list); decision: PreGrayFinalReviewDecision=PreGrayFinalReviewDecision.NEED_MORE_EVIDENCE; safety_note: str='材料复核只读生成，不代表实盘授权。'
@dataclass
class GoNoGoDraftReport: items: list[GoNoGoDraftItem]=field(default_factory=list); decision: GoNoGoDraftDecision=GoNoGoDraftDecision.NEED_MORE_EVIDENCE_DRAFT; safety_note: str='GO_DRAFT 不是实盘授权，仍不得自动实盘。'
@dataclass
class NoGoBlockerReport: items: list[NoGoBlockerItem]=field(default_factory=list); decision: PreGrayFinalReviewDecision=PreGrayFinalReviewDecision.NEED_MORE_EVIDENCE; safety_note: str='NO-GO 阻断清单只读生成。'
@dataclass
class GoConditionReport: items: list[GoConditionItem]=field(default_factory=list); decision: PreGrayFinalReviewDecision=PreGrayFinalReviewDecision.NEED_MORE_EVIDENCE; safety_note: str='GO 条件清单只是人工复核材料，不代表实盘授权。'
@dataclass
class Stage61ApiGatewayPlanReport: items: list[Stage61ApiGatewayPlanItem]=field(default_factory=list); decision: PreGrayFinalReviewDecision=PreGrayFinalReviewDecision.NEED_MORE_EVIDENCE; safety_note: str='Stage61 只搭本地 API 边界和只读查询接口，不接实盘。'

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj, list): return [to_plain(x) for x in obj]
    if isinstance(obj, dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj, Path): return str(obj)
    return obj
