from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any
class LiveGrayReadonlySealDecision(str,Enum): NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_READONLY_SEAL_REVIEW='READY_FOR_READONLY_SEAL_REVIEW'
class LiveGrayReadonlySealStatus(str,Enum): PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LiveGrayReadonlySealSeverity(str,Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LiveGrayReadonlySealCategory(str,Enum):
    STAGE58_FINAL_APPROVAL='STAGE58_FINAL_APPROVAL'; STAGE57_GRAY_CANDIDATE='STAGE57_GRAY_CANDIDATE'; STAGE56_REAL_CACHE_QUALITY='STAGE56_REAL_CACHE_QUALITY'; STAGE55_QMT_DRYRUN_CALIBRATION='STAGE55_QMT_DRYRUN_CALIBRATION'; APPROVAL_PACKAGE_LOCK='APPROVAL_PACKAGE_LOCK'; CONFIG_SUMMARY_LOCK='CONFIG_SUMMARY_LOCK'; RISK_RULE_LOCK='RISK_RULE_LOCK'; ETF_WHITELIST_LOCK='ETF_WHITELIST_LOCK'; ROLLBACK_CIRCUIT_LOCK='ROLLBACK_CIRCUIT_LOCK'; FINAL_SIGNOFF_RECHECK='FINAL_SIGNOFF_RECHECK'; PRE_RUN_CHECKLIST='PRE_RUN_CHECKLIST'; READONLY_SEAL_INDEX='READONLY_SEAL_INDEX'; MATERIAL_MANIFEST='MATERIAL_MANIFEST'; HASH_SUMMARY='HASH_SUMMARY'; ROADMAP_STAGE_PLAN='ROADMAP_STAGE_PLAN'; UI_PRODUCTIZATION_PLAN='UI_PRODUCTIZATION_PLAN'; QMT_BOUNDARY='QMT_BOUNDARY'; SCHEDULER_PREVIEW='SCHEDULER_PREVIEW'; NOTIFICATION_DRY_RUN='NOTIFICATION_DRY_RUN'; RUNTIME_ARTIFACT='RUNTIME_ARTIFACT'; SENSITIVE_FILE='SENSITIVE_FILE'; SYSTEM='SYSTEM'
@dataclass
class LiveGrayReadonlySealConfig:
    repo_root: str|Path='.'; output_dir: str|Path='live_gray_readonly_seal_stage59'; live_gray_final_approval_dir: str|Path='live_gray_final_approval_stage58'; live_gray_candidate_dir: str|Path='live_gray_candidate_stage57'; real_cache_quality_dir: str|Path='real_cache_quality_stage56'; qmt_dryrun_calibration_dir: str|Path='qmt_dryrun_calibration_stage55'; roadmap_path: str='docs/qmt-ai-trading-project-roadmap.md'
@dataclass
class LiveGrayReadonlySealEvidence:
    category: LiveGrayReadonlySealCategory=LiveGrayReadonlySealCategory.SYSTEM; status: LiveGrayReadonlySealStatus=LiveGrayReadonlySealStatus.SKIPPED; severity: LiveGrayReadonlySealSeverity=LiveGrayReadonlySealSeverity.INFO; title: str=''; summary: str=''; path: str=''; metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class ReadonlySealManifestItem:
    relative_path: str=''; exists: bool=False; size_bytes: int=0; sha256: str=''; category: LiveGrayReadonlySealCategory=LiveGrayReadonlySealCategory.MATERIAL_MANIFEST; required: bool=True
@dataclass
class PreRunChecklistItem:
    name: str=''; required: bool=True; status: LiveGrayReadonlySealStatus=LiveGrayReadonlySealStatus.WARN; summary: str='必须人工复核；不代表实盘授权'
@dataclass
class MaterialLockItem:
    name: str=''; status: LiveGrayReadonlySealStatus=LiveGrayReadonlySealStatus.WARN; summary: str='只读锁定，待人工复核；不代表实盘授权'
@dataclass
class FinalSignoffRecheckItem:
    role: str=''; required: bool=True; status: str='PENDING_MANUAL_SIGNOFF'; statement: str='未签字不得进入后续真实执行审批；本阶段不代表实盘授权'
@dataclass
class NextPreGrayReviewPlanItem:
    name: str=''; status: LiveGrayReadonlySealStatus=LiveGrayReadonlySealStatus.WARN; summary: str='Stage60 预灰度最终复核计划项；仍不自动实盘'
@dataclass
class LiveGrayReadonlySealReport:
    decision: LiveGrayReadonlySealDecision=LiveGrayReadonlySealDecision.NEED_MORE_EVIDENCE
    safety_note: str='本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_READONLY_SEAL_REVIEW 只表示灰度前只读封版与运行前检查清单材料可供人工复核。'
    evidence: list[LiveGrayReadonlySealEvidence]=field(default_factory=list); material_lock_items: list[MaterialLockItem]=field(default_factory=list); checklist_items: list[PreRunChecklistItem]=field(default_factory=list); manifest_items: list[ReadonlySealManifestItem]=field(default_factory=list); signoff_items: list[FinalSignoffRecheckItem]=field(default_factory=list); next_plan_items: list[NextPreGrayReviewPlanItem]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=dict)
@dataclass
class MaterialLockReport: items: list[MaterialLockItem]=field(default_factory=list); decision: LiveGrayReadonlySealDecision=LiveGrayReadonlySealDecision.NEED_MORE_EVIDENCE; safety_note: str='材料锁定报告只读生成，不代表实盘授权。'
@dataclass
class PreRunChecklistReport: items: list[PreRunChecklistItem]=field(default_factory=list); decision: LiveGrayReadonlySealDecision=LiveGrayReadonlySealDecision.NEED_MORE_EVIDENCE; safety_note: str='运行前检查清单只读生成，不调用交易接口。'
@dataclass
class ReadonlySealManifestReport: items: list[ReadonlySealManifestItem]=field(default_factory=list); decision: LiveGrayReadonlySealDecision=LiveGrayReadonlySealDecision.NEED_MORE_EVIDENCE; safety_note: str='manifest / hash 摘要只读生成，不扫描敏感文件。'
@dataclass
class FinalSignoffRecheckReport: items: list[FinalSignoffRecheckItem]=field(default_factory=list); decision: LiveGrayReadonlySealDecision=LiveGrayReadonlySealDecision.NEED_MORE_EVIDENCE; safety_note: str='最终签字状态复核只读生成；未签字不得进入后续真实执行审批。'
@dataclass
class NextPreGrayReviewPlanReport: items: list[NextPreGrayReviewPlanItem]=field(default_factory=list); decision: LiveGrayReadonlySealDecision=LiveGrayReadonlySealDecision.NEED_MORE_EVIDENCE; safety_note: str='Stage60 仍不能直接实盘，只做预灰度最终复核与 go/no-go 材料。'
def to_plain(obj: Any)->Any:
    if isinstance(obj,Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
