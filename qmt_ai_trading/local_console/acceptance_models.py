from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleAcceptanceDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW='READY_FOR_LOCAL_CONSOLE_UI_ACCEPTANCE_REVIEW'
class LocalConsoleAcceptanceStatus(str, Enum): PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleAcceptanceSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleAcceptanceFeatureType(str, Enum):
    UI_ACCEPTANCE_SUMMARY='UI_ACCEPTANCE_SUMMARY'; PAGE_INVENTORY='PAGE_INVENTORY'; FEATURE_INVENTORY='FEATURE_INVENTORY'; SAFETY_CHECKLIST='SAFETY_CHECKLIST'; OPEN_ITEMS='OPEN_ITEMS'; ACCEPTANCE_CONCLUSION_DRAFT='ACCEPTANCE_CONCLUSION_DRAFT'; ACCEPTANCE_PACKAGE_INDEX='ACCEPTANCE_PACKAGE_INDEX'; ROUTE_COVERAGE='ROUTE_COVERAGE'; ASSET_COVERAGE='ASSET_COVERAGE'; NEXT_STAGE_PLAN='NEXT_STAGE_PLAN'

@dataclass
class LocalConsoleAcceptanceConfig:
    repo_root: str='.'; output_dir: str='local_console_acceptance_stage72'; review_dir: str='local_console_review_stage71'; drilldown_dir: str='local_console_drilldown_stage70'; grouping_dir: str='local_console_grouping_stage69'; refresh_dir: str='local_console_refresh_stage68'; preview_dir: str='local_console_preview_stage67'; binding_dir: str='local_console_binding_stage66'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleAcceptanceEvidence:
    stage: str='Stage71'; path: str=''; status: LocalConsoleAcceptanceStatus=LocalConsoleAcceptanceStatus.UNAVAILABLE; decision: str=''; critical_count: int=0; summary: str=''; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class UiPageInventoryItem: route: str='#/ui-acceptance'; title: str='UI Acceptance Summary'; panel_id: str='ui-acceptance-summary-panel'; read_only: bool=True; note: str='本地只读页面，不是实盘授权。'
@dataclass
class UiFeatureInventoryItem: feature_id: str='ui-acceptance-summary'; feature_type: LocalConsoleAcceptanceFeatureType=LocalConsoleAcceptanceFeatureType.UI_ACCEPTANCE_SUMMARY; title: str='UI 验收汇总'; read_only: bool=True; note: str='只汇总材料状态，不写审批授权。'
@dataclass
class UiSafetyChecklistItem: item_id: str='stage72-readonly'; title: str='确认 Stage72 本地只读边界'; status: LocalConsoleAcceptanceStatus=LocalConsoleAcceptanceStatus.PASS; note: str='不下单，不调用 xttrader，不查询真实账户，不发送真实通知。'
@dataclass
class UiOpenItem: item_id: str='manual-review-required'; title: str='等待人工 UI 验收复核'; status: LocalConsoleAcceptanceStatus=LocalConsoleAcceptanceStatus.WARN; note: str='结论草稿不是 approval。'
@dataclass
class UiRouteCoverageItem: route: str='#/ui-acceptance'; allowed: bool=True; status: LocalConsoleAcceptanceStatus=LocalConsoleAcceptanceStatus.PASS; note: str='只读 hash route。'
@dataclass
class UiAssetCoverageItem: file_name: str='index.html'; status: LocalConsoleAcceptanceStatus=LocalConsoleAcceptanceStatus.PASS; note: str='静态只读 UI 资产。'
@dataclass
class AcceptanceConclusionDraft: decision: LocalConsoleAcceptanceDecision=LocalConsoleAcceptanceDecision.NEED_MORE_EVIDENCE; draft: str='验收结论草稿：仅表示本地控制台 UI 验收汇总材料可供人工复核，不是审批授权，不是交易授权。'; read_only: bool=True
@dataclass
class AcceptancePackageIndexItem: file_name: str='local_console_ui_acceptance_report.md'; title: str='Local Console UI Acceptance Report'; read_only: bool=True; note: str='只列本地验收材料，不触发任务。'
@dataclass
class UiAcceptanceSafetyFinding: marker: str=''; path: str=''; severity: LocalConsoleAcceptanceSeverity=LocalConsoleAcceptanceSeverity.INFO; context: str=''; note: str=''
@dataclass
class UiPageInventoryReport: items: list[UiPageInventoryItem]=field(default_factory=list)
@dataclass
class UiFeatureInventoryReport: items: list[UiFeatureInventoryItem]=field(default_factory=list)
@dataclass
class UiSafetyChecklistReport: items: list[UiSafetyChecklistItem]=field(default_factory=list)
@dataclass
class UiOpenItemsReport: items: list[UiOpenItem]=field(default_factory=list)
@dataclass
class UiRouteCoverageReport: items: list[UiRouteCoverageItem]=field(default_factory=list); forbidden_routes: list[str]=field(default_factory=list)
@dataclass
class UiAssetCoverageReport: items: list[UiAssetCoverageItem]=field(default_factory=list)
@dataclass
class AcceptanceConclusionDraftReport: conclusion: AcceptanceConclusionDraft=field(default_factory=AcceptanceConclusionDraft)
@dataclass
class AcceptancePackageIndexReport: items: list[AcceptancePackageIndexItem]=field(default_factory=list)
@dataclass
class UiAcceptanceSafetyReport: findings: list[UiAcceptanceSafetyFinding]=field(default_factory=list); critical_count: int=0; warnings: list[str]=field(default_factory=list)
@dataclass
class NextLocalHelpDocsPlanReport:
    stage: str='Stage73'; title: str='本地文档/帮助层'; items: list[str]=field(default_factory=lambda:['帮助文档','页面说明','功能说明','安全说明','FAQ','错误处理说明','Stage74 本地演示打包层计划']); safety_note: str='Stage73 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'
@dataclass
class UiAcceptanceSummaryReport:
    decision: LocalConsoleAcceptanceDecision=LocalConsoleAcceptanceDecision.NEED_MORE_EVIDENCE; read_only: bool=True; no_trade_authorization: bool=True; note: str='UI acceptance summary 只是本地验收材料，不是审批授权。'
@dataclass
class LocalConsoleUiAcceptanceReport:
    decision: LocalConsoleAcceptanceDecision=LocalConsoleAcceptanceDecision.NEED_MORE_EVIDENCE; config: LocalConsoleAcceptanceConfig=field(default_factory=LocalConsoleAcceptanceConfig); evidence: list[LocalConsoleAcceptanceEvidence]=field(default_factory=list); ui_summary: UiAcceptanceSummaryReport=field(default_factory=UiAcceptanceSummaryReport); page_inventory: list[UiPageInventoryItem]=field(default_factory=list); feature_inventory: list[UiFeatureInventoryItem]=field(default_factory=list); safety_checklist: list[UiSafetyChecklistItem]=field(default_factory=list); open_items: list[UiOpenItem]=field(default_factory=list); route_coverage: list[UiRouteCoverageItem]=field(default_factory=list); asset_coverage: list[UiAssetCoverageItem]=field(default_factory=list); conclusion_draft: AcceptanceConclusionDraft=field(default_factory=AcceptanceConclusionDraft); package_index: list[AcceptancePackageIndexItem]=field(default_factory=list); safety_findings: list[UiAcceptanceSafetyFinding]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':0})

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
