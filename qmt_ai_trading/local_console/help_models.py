from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleHelpDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW='READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW'
class LocalConsoleHelpStatus(str, Enum): PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleHelpSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleHelpFeatureType(str, Enum):
    HELP_HOME='HELP_HOME'; PAGE_HELP='PAGE_HELP'; FEATURE_HELP='FEATURE_HELP'; SAFETY_HELP='SAFETY_HELP'; FAQ='FAQ'; ERROR_HANDLING='ERROR_HANDLING'; GLOSSARY='GLOSSARY'; ROUTE_HELP_MAP='ROUTE_HELP_MAP'; HELP_PACKAGE_INDEX='HELP_PACKAGE_INDEX'; NEXT_STAGE_PLAN='NEXT_STAGE_PLAN'

@dataclass
class LocalConsoleHelpConfig:
    repo_root: str='.'; output_dir: str='local_console_help_stage73'; acceptance_dir: str='local_console_acceptance_stage72'; review_dir: str='local_console_review_stage71'; drilldown_dir: str='local_console_drilldown_stage70'; grouping_dir: str='local_console_grouping_stage69'; refresh_dir: str='local_console_refresh_stage68'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True
@dataclass
class LocalConsoleHelpEvidence:
    stage: str='Stage72'; path: str=''; status: LocalConsoleHelpStatus=LocalConsoleHelpStatus.UNAVAILABLE; decision: str=''; critical_count: int=0; summary: str=''; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class HelpHomeItem: item_id: str='help-home'; title: str='本地帮助首页'; body: str='本地只读控制台帮助首页，不是实盘授权。'; read_only: bool=True
@dataclass
class PageHelpItem: route: str='#/help'; title: str='页面说明'; body: str='该页面只展示本地帮助材料。'; read_only: bool=True
@dataclass
class FeatureHelpItem: feature_id: str='help-search'; feature_type: LocalConsoleHelpFeatureType=LocalConsoleHelpFeatureType.FEATURE_HELP; title: str='只读帮助搜索'; body: str='仅在本地帮助文本中搜索，不触发网络或交易动作。'; read_only: bool=True
@dataclass
class SafetyHelpItem: item_id: str='stage73-readonly'; title: str='安全边界'; body: str='不下单，不调用 xttrader，不查询真实账户，不发送真实通知。'; severity: LocalConsoleHelpSeverity=LocalConsoleHelpSeverity.INFO
@dataclass
class FaqItem: question: str='Stage73 是否是实盘授权？'; answer: str='不是。Stage73 只是本地文档/帮助层材料，不是审批授权，不会自动 approve。'
@dataclass
class ErrorHandlingItem: error_code: str='FORBIDDEN_ROUTE'; title: str='安全边界禁止路由'; resolution: str='显示只读错误占位，不发送网络请求，不执行危险 action。'
@dataclass
class GlossaryItem: term: str='READY_FOR_LOCAL_CONSOLE_HELP_DOCS_REVIEW'; definition: str='仅表示本地文档/帮助层材料可供人工复核，不是实盘授权。'
@dataclass
class RouteHelpMapItem: route: str='#/help'; panel: str='help-home-panel'; allowed: bool=True; note: str='只读帮助路由。'
@dataclass
class HelpPackageIndexItem: file_name: str='help_home.md'; title: str='Help Home'; read_only: bool=True; note: str='只列本地帮助材料，不触发任务。'
@dataclass
class DocsSafetyFinding: marker: str=''; path: str=''; severity: LocalConsoleHelpSeverity=LocalConsoleHelpSeverity.INFO; context: str=''; note: str=''
@dataclass
class HelpHomeReport: items: list[HelpHomeItem]=field(default_factory=list)
@dataclass
class PageHelpReport: items: list[PageHelpItem]=field(default_factory=list)
@dataclass
class FeatureHelpReport: items: list[FeatureHelpItem]=field(default_factory=list)
@dataclass
class SafetyHelpReport: items: list[SafetyHelpItem]=field(default_factory=list)
@dataclass
class FaqReport: items: list[FaqItem]=field(default_factory=list)
@dataclass
class ErrorHandlingReport: items: list[ErrorHandlingItem]=field(default_factory=list)
@dataclass
class GlossaryReport: items: list[GlossaryItem]=field(default_factory=list)
@dataclass
class RouteHelpMapReport: items: list[RouteHelpMapItem]=field(default_factory=list); forbidden_routes: list[str]=field(default_factory=list)
@dataclass
class HelpPackageIndexReport: items: list[HelpPackageIndexItem]=field(default_factory=list)
@dataclass
class DocsSafetyReport: findings: list[DocsSafetyFinding]=field(default_factory=list); critical_count: int=0; warnings: list[str]=field(default_factory=list)
@dataclass
class NextLocalDemoPackagePlanReport:
    stage: str='Stage74'; title: str='本地演示打包层'; items: list[str]=field(default_factory=lambda:['本地演示包目录','静态资源清单','演示入口页','只读 demo manifest','Stage75 UI 产品化收口计划']); safety_note: str='Stage74 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'
@dataclass
class LocalConsoleHelpDocsReport:
    decision: LocalConsoleHelpDecision=LocalConsoleHelpDecision.NEED_MORE_EVIDENCE; config: LocalConsoleHelpConfig=field(default_factory=LocalConsoleHelpConfig); evidence: list[LocalConsoleHelpEvidence]=field(default_factory=list); help_home: list[HelpHomeItem]=field(default_factory=list); page_help: list[PageHelpItem]=field(default_factory=list); feature_help: list[FeatureHelpItem]=field(default_factory=list); safety_help: list[SafetyHelpItem]=field(default_factory=list); faq: list[FaqItem]=field(default_factory=list); error_handling: list[ErrorHandlingItem]=field(default_factory=list); glossary: list[GlossaryItem]=field(default_factory=list); route_help_map: list[RouteHelpMapItem]=field(default_factory=list); help_package_index: list[HelpPackageIndexItem]=field(default_factory=list); docs_safety_findings: list[DocsSafetyFinding]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':0})

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
