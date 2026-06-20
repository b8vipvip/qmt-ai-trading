from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

class LocalConsoleShellDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW='READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW'
class LocalConsoleShellStatus(str, Enum):
    PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsoleShellSeverity(str, Enum):
    INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsoleShellAssetType(str, Enum):
    HTML='HTML'; JAVASCRIPT='JAVASCRIPT'; CSS='CSS'; MANIFEST='MANIFEST'; ROUTE_MAP='ROUTE_MAP'; DATA_BINDING_PLACEHOLDER='DATA_BINDING_PLACEHOLDER'; SAFETY_BANNER='SAFETY_BANNER'; NEXT_STAGE_PLAN='NEXT_STAGE_PLAN'

@dataclass
class LocalConsoleShellConfig:
    repo_root: str|Path='.'; output_dir: str|Path='local_console_shell_stage65'; local_console_dashboard_dir: str|Path='local_console_dashboard_stage64'; local_console_detail_dir: str|Path='local_console_detail_stage63'; local_console_dir: str|Path='local_console_stage62'; api_gateway_dir: str|Path='api_gateway_stage61'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; no_task_registered: bool=True
@dataclass
class LocalConsoleShellEvidence:
    stage: str=''; title: str=''; path: str=''; status: LocalConsoleShellStatus=LocalConsoleShellStatus.UNAVAILABLE; severity: LocalConsoleShellSeverity=LocalConsoleShellSeverity.WARN; summary: str=''; decision: str=''; critical_count: int=0; warning_count: int=0; blocking_reason_count: int=0; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class LocalConsoleShellAsset:
    name: str=''; path: str=''; asset_type: LocalConsoleShellAssetType=LocalConsoleShellAssetType.HTML; read_only: bool=True; sha256: str=''; summary: str=''
@dataclass
class LocalConsoleShellRoute:
    path: str=''; title: str=''; read_only: bool=True; enabled: bool=True; summary: str=''
@dataclass
class LocalConsoleDataBindingPlaceholder:
    placeholder_id: str=''; source: str=''; target_selector: str=''; stage66_binding_plan: str=''; read_only: bool=True
@dataclass
class LocalConsoleShellManifest:
    stage: str='Stage65'; title: str='本地控制台 shell / 静态页面骨架层'; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; assets: list[LocalConsoleShellAsset]=field(default_factory=list); warnings: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleShellReport:
    decision: LocalConsoleShellDecision=LocalConsoleShellDecision.NEED_MORE_EVIDENCE; safety_note: str='本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_LOCAL_CONSOLE_SHELL_REVIEW 只表示本地控制台 shell / 静态页面骨架层材料可供人工复核。'; evidence: list[LocalConsoleShellEvidence]=field(default_factory=list); assets: list[LocalConsoleShellAsset]=field(default_factory=list); routes: list[LocalConsoleShellRoute]=field(default_factory=list); data_binding_placeholders: list[LocalConsoleDataBindingPlaceholder]=field(default_factory=list); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':0})
@dataclass
class LocalConsoleShellRouteMapReport: routes: list[LocalConsoleShellRoute]=field(default_factory=list); forbidden_routes: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleShellAssetIndexReport: assets: list[LocalConsoleShellAsset]=field(default_factory=list); warnings: list[str]=field(default_factory=list)
@dataclass
class LocalConsoleDataBindingPlaceholderReport: placeholders: list[LocalConsoleDataBindingPlaceholder]=field(default_factory=list)
@dataclass
class LocalConsoleStaticSafetyReport:
    read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; no_task_registered: bool=True; items: list[str]=field(default_factory=lambda:['不调用 xttrader','不下单','不查询真实账户','不发送真实通知','不自动 approve','不绕过 Risk Gate','不绕过 Human Approval']); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class NextConsoleDataBindingPlanReport:
    stage: str='Stage66'; title: str='本地控制台静态数据绑定层'; safety_note: str='Stage66 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'; items: list[str]=field(default_factory=lambda:['绑定 Stage64 dashboard cards','绑定 Stage63 filters','绑定 Stage62 report list','绑定 Stage61 API capability','继续只读静态展示'])

def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj, list): return [to_plain(x) for x in obj]
    if isinstance(obj, dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj, Path): return str(obj)
    return obj
