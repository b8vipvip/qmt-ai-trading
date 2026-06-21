from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleGroupingDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW='READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW'
class LocalConsoleGroupingStatus(str, Enum): PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleGroupingSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleGroupingFeatureType(str, Enum):
    STATUS_GROUPING='STATUS_GROUPING'; STAGE_GROUPING='STAGE_GROUPING'; SEVERITY_GROUPING='SEVERITY_GROUPING'; WARNING_FILTER='WARNING_FILTER'; BLOCKING_REASON_FILTER='BLOCKING_REASON_FILTER'; READONLY_SEARCH='READONLY_SEARCH'; COLLAPSE_EXPAND='COLLAPSE_EXPAND'; COUNT_BADGE='COUNT_BADGE'; EMPTY_STATE='EMPTY_STATE'; NEXT_STAGE_PLAN='NEXT_STAGE_PLAN'

@dataclass
class LocalConsoleGroupingConfig:
    repo_root: str='.'; output_dir: str='local_console_grouping_stage69'; binding_dir: str='local_console_binding_stage66'; refresh_dir: str='local_console_refresh_stage68'; preview_dir: str='local_console_preview_stage67'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleGroupingEvidence:
    stage: str='Stage68'; path: str=''; status: LocalConsoleGroupingStatus=LocalConsoleGroupingStatus.UNAVAILABLE; decision: str=''; critical_count: int=0; summary: str=''; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class GroupingFilter:
    name: str='status'; values: list[str]=field(default_factory=list); read_only: bool=True
@dataclass
class GroupingFilterState:
    status: list[str]=field(default_factory=lambda:['PASS','WARN','FAIL','SKIPPED','UNAVAILABLE']); severity: list[str]=field(default_factory=lambda:['INFO','WARN','CRITICAL']); stage: list[str]=field(default_factory=lambda:[f'Stage{i}' for i in range(55,69)]); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); search: str=''
@dataclass
class GroupedCard:
    card_id: str='stage55-pass'; title: str='Stage55'; stage: str='Stage55'; status: str='PASS'; severity: str='INFO'; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); collapsed: bool=False
@dataclass
class GroupedCardIndex:
    cards: list[GroupedCard]=field(default_factory=list); status_groups: list[str]=field(default_factory=lambda:['PASS','WARN','FAIL','SKIPPED','UNAVAILABLE']); severity_groups: list[str]=field(default_factory=lambda:['INFO','WARN','CRITICAL']); stage_groups: list[str]=field(default_factory=lambda:[f'Stage{i}' for i in range(55,69)])
@dataclass
class SearchIndexItem:
    item_id: str='stage55'; title: str='Stage55'; content: str='read-only local console evidence'; route: str='#/dashboard'; tags: list[str]=field(default_factory=list)
@dataclass
class ReadOnlySearchConfig:
    selector: str='#readonly-search'; network_enabled: bool=False; placeholder: str='只读搜索，不发送网络请求'
@dataclass
class CollapseExpandConfig:
    selector: str='.grouped-card'; network_enabled: bool=False; default_collapsed: bool=False
@dataclass
class GroupingManifest:
    stage: str='Stage69'; assets: list[str]=field(default_factory=lambda:['index.html','app.js','style.css']); routes: list[str]=field(default_factory=list); read_only: bool=True; safety_banner: str='本地只读控制台｜不是实盘授权｜不下单｜不调用 xttrader｜不查询真实账户｜不发送真实通知'
@dataclass
class GroupingFrontendSafetyFinding:
    marker: str=''; path: str=''; severity: LocalConsoleGroupingSeverity=LocalConsoleGroupingSeverity.INFO; context: str=''; note: str=''
@dataclass
class LocalConsoleGroupingReport:
    decision: LocalConsoleGroupingDecision=LocalConsoleGroupingDecision.NEED_MORE_EVIDENCE; config: LocalConsoleGroupingConfig=field(default_factory=LocalConsoleGroupingConfig); evidence: list[LocalConsoleGroupingEvidence]=field(default_factory=list); manifest: GroupingManifest=field(default_factory=GroupingManifest); filter_state: GroupingFilterState=field(default_factory=GroupingFilterState); card_index: GroupedCardIndex=field(default_factory=GroupedCardIndex); search_index: list[SearchIndexItem]=field(default_factory=list); safety_findings: list[GroupingFrontendSafetyFinding]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':0})
@dataclass
class GroupingFilterStateReport: filter_state: GroupingFilterState=field(default_factory=GroupingFilterState)
@dataclass
class GroupedCardIndexReport: card_index: GroupedCardIndex=field(default_factory=GroupedCardIndex)
@dataclass
class SearchIndexReport: items: list[SearchIndexItem]=field(default_factory=list)
@dataclass
class GroupingFrontendSafetyReport: findings: list[GroupingFrontendSafetyFinding]=field(default_factory=list); critical_count: int=0; warnings: list[str]=field(default_factory=list)
@dataclass
class NextConsoleDrilldownExportPlanReport:
    stage: str='Stage70'; title: str='本地控制台报告详情钻取与导出层'; items: list[str]=field(default_factory=lambda:['报告详情钻取','单报告预览','复制摘要','导出本地 Markdown/JSON 快照','错误报告定位','人工复核包入口']); safety_note: str='Stage70 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
