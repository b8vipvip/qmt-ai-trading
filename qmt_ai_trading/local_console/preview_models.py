from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any
class LocalConsolePreviewDecision(str, Enum):
    NO_GO='NO_GO'; NEED_MORE_EVIDENCE='NEED_MORE_EVIDENCE'; READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW='READY_FOR_LOCAL_CONSOLE_PREVIEW_REVIEW'
class LocalConsolePreviewStatus(str, Enum):
    PASS='PASS'; WARN='WARN'; FAIL='FAIL'; SKIPPED='SKIPPED'; UNAVAILABLE='UNAVAILABLE'
class LocalConsolePreviewSeverity(str, Enum): INFO='INFO'; WARN='WARN'; CRITICAL='CRITICAL'
class LocalConsolePreviewRouteType(str, Enum):
    STATIC_HTML='STATIC_HTML'; STATIC_JS='STATIC_JS'; STATIC_CSS='STATIC_CSS'; STATIC_JSON='STATIC_JSON'; HEALTH='HEALTH'; MANIFEST='MANIFEST'; SAFETY='SAFETY'; NEXT_STAGE_PLAN='NEXT_STAGE_PLAN'
@dataclass
class LocalConsolePreviewConfig:
    repo_root: str='.'; static_dir: str='local_console_binding_stage66'; host: str='127.0.0.1'; port: int=8767; dry_run: bool=True; serve_once: bool=False; timeout_seconds: int=5
@dataclass
class LocalConsolePreviewEvidence:
    stage: str='Stage66'; path: str=''; status: LocalConsolePreviewStatus=LocalConsolePreviewStatus.UNAVAILABLE; decision: str=''; critical_count: int=0; summary: str=''; encoding_warning: bool=False; warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list)
@dataclass
class PreviewRoute:
    path: str='/'; methods: list[str]=field(default_factory=lambda:['GET','HEAD']); route_type: LocalConsolePreviewRouteType=LocalConsolePreviewRouteType.STATIC_HTML; allowed: bool=True; severity: LocalConsolePreviewSeverity=LocalConsolePreviewSeverity.INFO; note: str='read-only'
@dataclass
class PreviewStaticFile:
    path: str=''; exists: bool=False; size: int=0; route: str=''; content_type: str=''; encoding_warning: bool=False; warnings: list[str]=field(default_factory=list)
@dataclass
class PreviewResponseManifest:
    route: str=''; methods: list[str]=field(default_factory=lambda:['GET','HEAD']); status: int=200; read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; source_file: str=''
@dataclass
class PreviewSafetyBoundary:
    read_only: bool=True; dry_run_only: bool=True; no_trade_authorization: bool=True; host: str='127.0.0.1'; public_bind: bool=False; allowed_methods: list[str]=field(default_factory=lambda:['GET','HEAD']); forbidden_methods: list[str]=field(default_factory=lambda:['POST','PUT','PATCH','DELETE']); critical_findings: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list)
@dataclass
class PreviewServerReport:
    decision: LocalConsolePreviewDecision=LocalConsolePreviewDecision.NEED_MORE_EVIDENCE; config: LocalConsolePreviewConfig=field(default_factory=LocalConsolePreviewConfig); evidence: list[LocalConsolePreviewEvidence]=field(default_factory=list); routes: list[PreviewRoute]=field(default_factory=list); static_files: list[PreviewStaticFile]=field(default_factory=list); response_manifest: list[PreviewResponseManifest]=field(default_factory=list); safety_boundary: PreviewSafetyBoundary=field(default_factory=PreviewSafetyBoundary); warnings: list[str]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=lambda:{'read_only':True,'dry_run_only':True,'no_trade_authorization':True,'critical_count':0})
@dataclass
class PreviewRouteMapReport: routes: list[PreviewRoute]=field(default_factory=list); forbidden_routes: list[str]=field(default_factory=list)
@dataclass
class PreviewStaticFileIndexReport: files: list[PreviewStaticFile]=field(default_factory=list)
@dataclass
class PreviewResponseManifestReport: responses: list[PreviewResponseManifest]=field(default_factory=list)
@dataclass
class PreviewSafetyReport: boundary: PreviewSafetyBoundary=field(default_factory=PreviewSafetyBoundary)
@dataclass
class NextConsoleRefreshPlanReport:
    stage: str='Stage68'; title: str='本地控制台刷新与导航增强层'; items: list[str]=field(default_factory=lambda:['只读刷新按钮','hash route 只读导航','错误占位','数据更新时间显示','静态 bundle 重载体验']); safety_note: str='Stage68 仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单。'
def to_plain(obj: Any)->Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj,'__dataclass_fields__'): return {k:to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj,list): return [to_plain(x) for x in obj]
    if isinstance(obj,dict): return {k:to_plain(v) for k,v in obj.items()}
    if isinstance(obj,Path): return str(obj)
    return obj
