from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleReviewDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_REVIEW_WORKBENCH_REVIEW='READY_FOR_LOCAL_CONSOLE_REVIEW_WORKBENCH_REVIEW'
class LocalConsoleReviewStatus(str, Enum): PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleReviewSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleReviewState(str, Enum): PENDING_REVIEW='PENDING_REVIEW'; REVIEWED='REVIEWED'; NEEDS_FIX='NEEDS_FIX'
class LocalConsoleReviewFeatureType(str, Enum):
    REVIEW_WORKBENCH='REVIEW_WORKBENCH'; REVIEW_CHECKLIST='REVIEW_CHECKLIST'; REVIEW_NOTES_TEMPLATE='REVIEW_NOTES_TEMPLATE'; LOCAL_CONFIRMATION_CHECKLIST='LOCAL_CONFIRMATION_CHECKLIST'; REVIEW_PACKAGE_INDEX='REVIEW_PACKAGE_INDEX'; REVIEW_STATUS_PLACEHOLDER='REVIEW_STATUS_PLACEHOLDER'; REVIEW_CONCLUSION_DRAFT='REVIEW_CONCLUSION_DRAFT'; REVIEW_SAFETY='REVIEW_SAFETY'; NEXT_STAGE_PLAN='NEXT_STAGE_PLAN'

@dataclass
class LocalConsoleReviewConfig:
    repo_root: str='.'; output_dir: str='local_console_review_stage71'; drilldown_dir: str='local_console_drilldown_stage70'; grouping_dir: str='local_console_grouping_stage69'; refresh_dir: str='local_console_refresh_stage68'; preview_dir: str='local_console_preview_stage67'; binding_dir: str='local_console_binding_stage66'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleReviewEvidence:
    stage: str='Stage70'; path: str=''; status: LocalConsoleReviewStatus=LocalConsoleReviewStatus.UNAVAILABLE; decision: str=''; critical_count: int=0; summary: str=''; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class ReviewChecklistItem:
    item_id: str='review-readonly-boundary'; title: str='确认本地只读边界'; required: bool=True; state: LocalConsoleReviewState=LocalConsoleReviewState.PENDING_REVIEW; note: str='确认清单不是交易授权。'
@dataclass
class ReviewNotesTemplate:
    template_id: str='stage71-review-notes'; title: str='Stage71 Review Notes Template'; body: str='本模板只是人工复核草稿，不是审批授权，不下单，不调用 xttrader。'; read_only: bool=True
@dataclass
class LocalConfirmationItem:
    item_id: str='confirm-not-live'; title: str='确认不是实盘授权'; required: bool=True; note: str='本地确认项不是交易授权。'
@dataclass
class ReviewPackageIndexItem:
    file_name: str='local_console_review_workbench_report.md'; title: str='Review Workbench Report'; read_only: bool=True; note: str='只列本地复核材料，不触发任务。'
@dataclass
class ReviewStatusPlaceholder:
    state: LocalConsoleReviewState=LocalConsoleReviewState.PENDING_REVIEW; note: str='状态占位仅供人工复核记录，不自动 approve。'
@dataclass
class ReviewConclusionDraft:
    decision: LocalConsoleReviewDecision=LocalConsoleReviewDecision.NEED_MORE_EVIDENCE; draft: str='复核结论草稿：仅供人工复核，不是实盘授权。'
@dataclass
class ReviewSafetyFinding:
    marker: str=''; path: str=''; severity: LocalConsoleReviewSeverity=LocalConsoleReviewSeverity.INFO; context: str=''; note: str=''
@dataclass
class LocalConsoleReviewWorkbenchReport:
    decision: LocalConsoleReviewDecision=LocalConsoleReviewDecision.NEED_MORE_EVIDENCE; config: LocalConsoleReviewConfig=field(default_factory=LocalConsoleReviewConfig); evidence: list[LocalConsoleReviewEvidence]=field(default_factory=list); checklist: list[ReviewChecklistItem]=field(default_factory=list); notes_template: ReviewNotesTemplate=field(default_factory=ReviewNotesTemplate); confirmations: list[LocalConfirmationItem]=field(default_factory=list); package_index: list[ReviewPackageIndexItem]=field(default_factory=list); status_placeholder: ReviewStatusPlaceholder=field(default_factory=ReviewStatusPlaceholder); conclusion_draft: ReviewConclusionDraft=field(default_factory=ReviewConclusionDraft); safety_findings: list[ReviewSafetyFinding]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':0})
@dataclass
class ReviewManifestReport: stage: str='Stage71'; assets: list[str]=field(default_factory=list); routes: list[str]=field(default_factory=list); read_only: bool=True
@dataclass
class ReviewChecklistReport: items: list[ReviewChecklistItem]=field(default_factory=list)
@dataclass
class ReviewNotesTemplateReport: template: ReviewNotesTemplate=field(default_factory=ReviewNotesTemplate)
@dataclass
class LocalConfirmationChecklistReport: items: list[LocalConfirmationItem]=field(default_factory=list)
@dataclass
class ReviewPackageIndexReport: items: list[ReviewPackageIndexItem]=field(default_factory=list)
@dataclass
class ReviewSafetyReport: findings: list[ReviewSafetyFinding]=field(default_factory=list); critical_count: int=0; warnings: list[str]=field(default_factory=list)
@dataclass
class NextUiAcceptanceSummaryPlanReport:
    stage: str='Stage72'; title: str='本地控制台 UI 验收汇总层'; items: list[str]=field(default_factory=lambda:['UI 验收汇总','页面清单','功能清单','安全清单','未完成项清单','Stage73 本地文档/帮助层计划']); safety_note: str='Stage72 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
