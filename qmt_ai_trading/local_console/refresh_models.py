from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleRefreshDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW='READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW'
class LocalConsoleRefreshStatus(str, Enum):
    PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleRefreshSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleRefreshFeatureType(str, Enum):
    HASH_NAVIGATION='HASH_NAVIGATION'; READONLY_REFRESH='READONLY_REFRESH'; DATA_BUNDLE_RELOAD='DATA_BUNDLE_RELOAD'; UPDATED_AT_DISPLAY='UPDATED_AT_DISPLAY'; LOADING_STATE='LOADING_STATE'; ERROR_STATE='ERROR_STATE'; EMPTY_STATE='EMPTY_STATE'; SAFETY_BANNER='SAFETY_BANNER'; NEXT_STAGE_PLAN='NEXT_STAGE_PLAN'

@dataclass
class LocalConsoleRefreshConfig:
    repo_root: str='.'; output_dir: str='local_console_refresh_stage68'; binding_dir: str='local_console_binding_stage66'; preview_dir: str='local_console_preview_stage67'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleRefreshEvidence:
    stage: str='Stage67'; path: str=''; status: LocalConsoleRefreshStatus=LocalConsoleRefreshStatus.UNAVAILABLE; decision: str=''; critical_count: int=0; summary: str=''; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class RefreshFeature:
    name: str=''; feature_type: LocalConsoleRefreshFeatureType=LocalConsoleRefreshFeatureType.HASH_NAVIGATION; status: LocalConsoleRefreshStatus=LocalConsoleRefreshStatus.PASS; read_only: bool=True; note: str=''
@dataclass
class NavigationRoute:
    hash_route: str='#/dashboard'; title: str='Dashboard'; allowed: bool=True; severity: LocalConsoleRefreshSeverity=LocalConsoleRefreshSeverity.INFO; note: str='read-only route'
@dataclass
class ReadonlyRefreshAction:
    name: str='reloadDataBundle'; allowed_sources: list[str]=field(default_factory=lambda:['./data_bundle.json','./binding_manifest.json','./data_source_map.json','./static_data_safety.json']); read_only: bool=True
@dataclass
class UiStatePlaceholder:
    state: str='loading'; selector: str='#loading-state'; message: str='Loading local read-only bundle'; status: LocalConsoleRefreshStatus=LocalConsoleRefreshStatus.PASS
@dataclass
class RefreshManifest:
    stage: str='Stage68'; assets: list[str]=field(default_factory=lambda:['index.html','app.js','style.css']); read_only: bool=True; safety_banner: str='本地只读控制台｜不是实盘授权｜不下单｜不调用 xttrader｜不查询真实账户｜不发送真实通知'
@dataclass
class FrontEndSafetyFinding:
    marker: str=''; path: str=''; severity: LocalConsoleRefreshSeverity=LocalConsoleRefreshSeverity.INFO; context: str=''; note: str=''
@dataclass
class LocalConsoleRefreshReport:
    decision: LocalConsoleRefreshDecision=LocalConsoleRefreshDecision.NEED_MORE_EVIDENCE; config: LocalConsoleRefreshConfig=field(default_factory=LocalConsoleRefreshConfig); evidence: list[LocalConsoleRefreshEvidence]=field(default_factory=list); features: list[RefreshFeature]=field(default_factory=list); routes: list[NavigationRoute]=field(default_factory=list); refresh_action: ReadonlyRefreshAction=field(default_factory=ReadonlyRefreshAction); ui_states: list[UiStatePlaceholder]=field(default_factory=list); safety_findings: list[FrontEndSafetyFinding]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':0})
@dataclass
class NavigationRouteMapReport: routes: list[NavigationRoute]=field(default_factory=list); forbidden_routes: list[str]=field(default_factory=list)
@dataclass
class RefreshManifestReport: manifest: RefreshManifest=field(default_factory=RefreshManifest)
@dataclass
class UiStatePlaceholderReport: states: list[UiStatePlaceholder]=field(default_factory=list)
@dataclass
class FrontEndSafetyReport: findings: list[FrontEndSafetyFinding]=field(default_factory=list); critical_count: int=0; warnings: list[str]=field(default_factory=list)
@dataclass
class NextConsoleGroupingFilterPlanReport:
    stage: str='Stage69'; title: str='本地控制台状态分组与筛选体验层'; items: list[str]=field(default_factory=lambda:['状态分组','阶段筛选','warning 筛选','blocking reason 筛选','只读搜索','卡片折叠/展开']); safety_note: str='Stage69 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
