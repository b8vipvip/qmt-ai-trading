from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleDemoDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW='READY_FOR_LOCAL_CONSOLE_DEMO_PACKAGE_REVIEW'
class LocalConsoleDemoStatus(str, Enum): PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleDemoSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleDemoFeatureType(str, Enum):
    DEMO_HOME='DEMO_HOME'; DEMO_INDEX='DEMO_INDEX'; DEMO_GUIDE='DEMO_GUIDE'; DEMO_MANIFEST='DEMO_MANIFEST'; DEMO_ROUTE_MAP='DEMO_ROUTE_MAP'; DEMO_ASSET_MANIFEST='DEMO_ASSET_MANIFEST'; DEMO_PACKAGE_INDEX='DEMO_PACKAGE_INDEX'; DEMO_SAFETY='DEMO_SAFETY'; DEMO_VALIDATION_SUMMARY='DEMO_VALIDATION_SUMMARY'; NEXT_STAGE_PLAN='NEXT_STAGE_PLAN'

@dataclass
class LocalConsoleDemoConfig:
    repo_root: str='.'; output_dir: str='local_console_demo_stage74'; help_dir: str='local_console_help_stage73'; acceptance_dir: str='local_console_acceptance_stage72'; review_dir: str='local_console_review_stage71'; drilldown_dir: str='local_console_drilldown_stage70'; grouping_dir: str='local_console_grouping_stage69'; refresh_dir: str='local_console_refresh_stage68'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleDemoEvidence:
    stage: str='Stage73'; path: str=''; status: LocalConsoleDemoStatus=LocalConsoleDemoStatus.UNAVAILABLE; decision: str=''; critical_count: int=0; summary: str=''; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class DemoHomeItem: item_id: str='demo-home'; title: str='本地演示首页'; body: str='本地只读控制台演示首页，不是实盘授权。'; read_only: bool=True
@dataclass
class DemoStaticAssetItem: file_name: str='index.html'; asset_type: str='html'; title: str='演示入口页'; read_only: bool=True; note: str='静态只读资产。'
@dataclass
class DemoRouteMapItem: route: str='#/demo'; panel: str='demo-home-panel'; allowed: bool=True; note: str='只读演示路由。'
@dataclass
class DemoManifest: package_name: str='local_console_demo_stage74'; title: str='Stage74 本地演示打包层'; safety_note: str='本地演示包只是静态演示材料，不是审批授权，不是交易授权。'; files: list[str]=field(default_factory=list); read_only: bool=True
@dataclass
class DemoGuideItem: title: str='演示说明'; body: str='demo guide 只是本地只读演示说明，不是审批授权，不下单。'; read_only: bool=True
@dataclass
class DemoPackageIndexItem: file_name: str='demo_manifest.md'; title: str='Demo Manifest'; read_only: bool=True; note: str='只列本地演示材料，不触发任务。'
@dataclass
class DemoSafetyFinding: marker: str=''; path: str=''; severity: LocalConsoleDemoSeverity=LocalConsoleDemoSeverity.INFO; context: str=''; note: str=''
@dataclass
class DemoValidationSummary: status: LocalConsoleDemoStatus=LocalConsoleDemoStatus.PASS; message: str='本地演示包只读验证通过。'; critical_count: int=0
@dataclass
class DemoManifestReport: manifest: DemoManifest=field(default_factory=DemoManifest)
@dataclass
class DemoGuideReport: items: list[DemoGuideItem]=field(default_factory=list)
@dataclass
class DemoRouteMapReport: items: list[DemoRouteMapItem]=field(default_factory=list); forbidden_routes: list[str]=field(default_factory=list)
@dataclass
class DemoAssetManifestReport: items: list[DemoStaticAssetItem]=field(default_factory=list)
@dataclass
class DemoPackageIndexReport: items: list[DemoPackageIndexItem]=field(default_factory=list)
@dataclass
class DemoSafetyReport: findings: list[DemoSafetyFinding]=field(default_factory=list); critical_count: int=0; warnings: list[str]=field(default_factory=list)
@dataclass
class DemoValidationSummaryReport: summary: DemoValidationSummary=field(default_factory=DemoValidationSummary); checks: list[str]=field(default_factory=list)
@dataclass
class NextUiProductizationClosurePlanReport:
    stage: str='Stage75'; title: str='UI 产品化收口层'; items: list[str]=field(default_factory=lambda:['阶段总览','UI 能力矩阵','安全边界总表','只读演示入口','最终验收结论草稿']); safety_note: str='Stage75 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'
@dataclass
class LocalConsoleDemoPackageReport:
    decision: LocalConsoleDemoDecision=LocalConsoleDemoDecision.NEED_MORE_EVIDENCE; config: LocalConsoleDemoConfig=field(default_factory=LocalConsoleDemoConfig); evidence: list[LocalConsoleDemoEvidence]=field(default_factory=list); demo_home: list[DemoHomeItem]=field(default_factory=list); demo_manifest: DemoManifest=field(default_factory=DemoManifest); demo_guide: list[DemoGuideItem]=field(default_factory=list); demo_route_map: list[DemoRouteMapItem]=field(default_factory=list); demo_asset_manifest: list[DemoStaticAssetItem]=field(default_factory=list); demo_package_index: list[DemoPackageIndexItem]=field(default_factory=list); demo_safety_findings: list[DemoSafetyFinding]=field(default_factory=list); demo_validation_summary: DemoValidationSummary=field(default_factory=DemoValidationSummary); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':0})

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
