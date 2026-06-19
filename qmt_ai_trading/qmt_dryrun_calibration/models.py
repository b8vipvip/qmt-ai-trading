# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
SAFETY_NOTE="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW 只表示 QMT 实机 dry-run 环境校准材料可供人工复核。"
class QmtDryrunCalibrationDecision(str, Enum):
    NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW="READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW"
class QmtDryrunCalibrationStatus(str, Enum): PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"; UNAVAILABLE="UNAVAILABLE"
class QmtDryrunCalibrationSeverity(str, Enum): INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class QmtDryrunCalibrationCategory(str, Enum):
    STAGE54_GAP_CLEARANCE="STAGE54_GAP_CLEARANCE"; QMT_PATH="QMT_PATH"; XTQUANT_IMPORT="XTQUANT_IMPORT"; XTDATA_IMPORT="XTDATA_IMPORT"; XTDATA_FUNCTION="XTDATA_FUNCTION"; XTDATA_SMOKE_TEST="XTDATA_SMOKE_TEST"; CACHE_ROUNDTRIP="CACHE_ROUNDTRIP"; FIELD_MAPPING="FIELD_MAPPING"; TRADING_DAY_TIME="TRADING_DAY_TIME"; ETF_WHITELIST="ETF_WHITELIST"; ROADMAP_STAGE_PLAN="ROADMAP_STAGE_PLAN"; UI_PRODUCTIZATION_PLAN="UI_PRODUCTIZATION_PLAN"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"
def enum_value(v): return v.value if isinstance(v, Enum) else v
def to_plain(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k:to_plain(x) for k,x in asdict(v).items()}
    if isinstance(v, dict): return {str(k):to_plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [to_plain(x) for x in v]
    return v
@dataclass
class QmtDryrunCalibrationConfig:
    repo_root:str="."; output_dir:str="qmt_dryrun_calibration_stage55"; gap_clearance_dir:str="live_gap_clearance_stage54"; cache_root:str="market_data_test_stage55"; provider:str="mock"; max_symbols:int=5; max_days:int=90; roadmap_path:str="docs/qmt-ai-trading-project-roadmap.md"; validation_logs_dir:str="validation_logs"; read_only:bool=True; dry_run_only:bool=True; no_trade_authorization:bool=True; live_trading_enabled:bool=False; no_task_registered:bool=True; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class QmtDryrunCalibrationEvidence:
    evidence_id:str="stage55-evidence"; category:QmtDryrunCalibrationCategory|str=QmtDryrunCalibrationCategory.SYSTEM; status:QmtDryrunCalibrationStatus|str=QmtDryrunCalibrationStatus.SKIPPED; severity:QmtDryrunCalibrationSeverity|str=QmtDryrunCalibrationSeverity.WARN; path:str=""; title:str=""; summary:str=""; decision:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class QmtPathCheckItem: item_id:str="qmt-path"; title:str=""; status:QmtDryrunCalibrationStatus|str=QmtDryrunCalibrationStatus.WARN; summary:str=""; path:str=""; exists:bool=False
@dataclass
class XtdataCapabilityItem: item_id:str="xtdata"; name:str=""; status:QmtDryrunCalibrationStatus|str=QmtDryrunCalibrationStatus.UNAVAILABLE; summary:str=""; available:bool=False
@dataclass
class CacheRoundtripItem: item_id:str="cache"; title:str=""; status:QmtDryrunCalibrationStatus|str=QmtDryrunCalibrationStatus.SKIPPED; summary:str=""; path:str=""
@dataclass
class FieldMappingItem: item_id:str="field"; field_name:str=""; status:QmtDryrunCalibrationStatus|str=QmtDryrunCalibrationStatus.PASS; source_name:str=""; summary:str=""
@dataclass
class EtfWhitelistItem: item_id:str="etf"; symbol:str=""; status:QmtDryrunCalibrationStatus|str=QmtDryrunCalibrationStatus.PASS; summary:str=""
@dataclass
class NextRealCacheQualityPlanItem: item_id:str="plan"; title:str=""; status:QmtDryrunCalibrationStatus|str=QmtDryrunCalibrationStatus.PASS; summary:str=""
@dataclass
class QmtDryrunCalibrationReport:
    report_id:str="stage55-qmt-dryrun-calibration"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:QmtDryrunCalibrationDecision|str=QmtDryrunCalibrationDecision.NEED_MORE_EVIDENCE; config:QmtDryrunCalibrationConfig|dict[str,Any]=field(default_factory=QmtDryrunCalibrationConfig); evidence:list[QmtDryrunCalibrationEvidence]=field(default_factory=list); qmt_paths:list[QmtPathCheckItem]=field(default_factory=list); xtdata_capabilities:list[XtdataCapabilityItem]=field(default_factory=list); cache_roundtrip:list[CacheRoundtripItem]=field(default_factory=list); field_mapping:list[FieldMappingItem]=field(default_factory=list); etf_whitelist:list[EtfWhitelistItem]=field(default_factory=list); next_real_cache_quality_plan:list[NextRealCacheQualityPlanItem]=field(default_factory=list); required_manual_confirmations:list[str]=field(default_factory=lambda:["确认 Stage55 不代表实盘授权","确认不调用 xttrader、不查账户、不下单、不真实通知","确认 READY_FOR_QMT_DRYRUN_CALIBRATION_REVIEW 仅代表材料可供人工复核"]); blocking_reasons:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); safety_note:str=SAFETY_NOTE; summary:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return to_plain(self)
@dataclass
class XtdataCapabilityReport: report_id:str="stage55-xtdata-capability"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:QmtDryrunCalibrationDecision|str=QmtDryrunCalibrationDecision.NEED_MORE_EVIDENCE; items:list[XtdataCapabilityItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
@dataclass
class EtfWhitelistCalibrationReport: report_id:str="stage55-etf-whitelist"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:QmtDryrunCalibrationDecision|str=QmtDryrunCalibrationDecision.NEED_MORE_EVIDENCE; items:list[EtfWhitelistItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
@dataclass
class NextRealCacheQualityPlanReport: report_id:str="stage55-next-real-cache-quality-plan"; created_at:str=field(default_factory=lambda: datetime.now(timezone.utc).isoformat()); decision:QmtDryrunCalibrationDecision|str=QmtDryrunCalibrationDecision.NEED_MORE_EVIDENCE; items:list[NextRealCacheQualityPlanItem]=field(default_factory=list); safety_note:str=SAFETY_NOTE; warnings:list[str]=field(default_factory=list); blocking_reasons:list[str]=field(default_factory=list); summary:dict[str,Any]=field(default_factory=dict)
