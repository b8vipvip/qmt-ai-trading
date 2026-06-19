from __future__ import annotations
from dataclasses import dataclass, field, asdict
import dataclasses as dc
from enum import Enum
from pathlib import Path
from typing import Any

class RealCacheQualityDecision(str, Enum):
    NO_GO="NO_GO"; NEED_MORE_EVIDENCE="NEED_MORE_EVIDENCE"; READY_FOR_REAL_CACHE_QUALITY_REVIEW="READY_FOR_REAL_CACHE_QUALITY_REVIEW"
class RealCacheQualityStatus(str, Enum):
    PASS="PASS"; WARN="WARN"; FAIL="FAIL"; SKIPPED="SKIPPED"; UNAVAILABLE="UNAVAILABLE"
class RealCacheQualitySeverity(str, Enum):
    INFO="INFO"; WARN="WARN"; CRITICAL="CRITICAL"
class RealCacheQualityCategory(str, Enum):
    STAGE55_QMT_DRYRUN_CALIBRATION="STAGE55_QMT_DRYRUN_CALIBRATION"; CACHE_COVERAGE="CACHE_COVERAGE"; LONG_SAMPLE_COMPLETENESS="LONG_SAMPLE_COMPLETENESS"; MISSING_VALUE="MISSING_VALUE"; DUPLICATE_BAR="DUPLICATE_BAR"; OHLC_VALIDITY="OHLC_VALIDITY"; VOLUME_AMOUNT_VALIDITY="VOLUME_AMOUNT_VALIDITY"; TRADING_DAY_TIME="TRADING_DAY_TIME"; SUSPENSION_OR_NO_TRADE="SUSPENSION_OR_NO_TRADE"; ADJUSTMENT_CONSISTENCY="ADJUSTMENT_CONSISTENCY"; FIELD_MAPPING="FIELD_MAPPING"; ETF_WHITELIST="ETF_WHITELIST"; ROADMAP_STAGE_PLAN="ROADMAP_STAGE_PLAN"; UI_PRODUCTIZATION_PLAN="UI_PRODUCTIZATION_PLAN"; HUMAN_APPROVAL="HUMAN_APPROVAL"; RISK_GATE="RISK_GATE"; QMT_BOUNDARY="QMT_BOUNDARY"; SCHEDULER_PREVIEW="SCHEDULER_PREVIEW"; NOTIFICATION_DRY_RUN="NOTIFICATION_DRY_RUN"; RUNTIME_ARTIFACT="RUNTIME_ARTIFACT"; SENSITIVE_FILE="SENSITIVE_FILE"; SYSTEM="SYSTEM"

@dataclass
class RealCacheQualityConfig:
    repo_root: str|Path = "."; output_dir: str|Path = "real_cache_quality_stage56"; qmt_dryrun_calibration_dir: str|Path = "qmt_dryrun_calibration_stage55"; cache_root: str|Path = "market_data_test_stage56"; provider: str = "mock"; max_symbols: int = 5; min_days: int = 40; target_days: int = 90; frequency: str = "1d"; roadmap_path: str = "docs/qmt-ai-trading-project-roadmap.md"
@dataclass
class RealCacheQualityEvidence:
    category: RealCacheQualityCategory = RealCacheQualityCategory.SYSTEM; status: RealCacheQualityStatus = RealCacheQualityStatus.SKIPPED; severity: RealCacheQualitySeverity = RealCacheQualitySeverity.INFO; title: str = ""; summary: str = ""; path: str = ""; metadata: dict[str, Any] = field(default_factory=dict)
@dataclass
class CacheCoverageItem:
    symbol: str=""; bar_count: int=0; start_date: str=""; end_date: str=""; status: RealCacheQualityStatus=RealCacheQualityStatus.UNAVAILABLE; summary: str=""
@dataclass
class LongSampleCompletenessItem:
    symbol: str=""; required_days: int=0; actual_days: int=0; missing_days: list[str]=field(default_factory=list); status: RealCacheQualityStatus=RealCacheQualityStatus.UNAVAILABLE; summary: str=""
@dataclass
class FieldQualityItem:
    symbol: str=""; field: str=""; status: RealCacheQualityStatus=RealCacheQualityStatus.PASS; issue_count: int=0; summary: str=""; examples: list[str]=dc.field(default_factory=list)
@dataclass
class GapFillPlanItem:
    symbol: str=""; target_days: int=90; current_days: int=0; missing_summary: str=""; action: str="mock roundtrip validated; future xtdata read-only fill only"
@dataclass
class NextBacktestAttributionPlanItem:
    name: str=""; summary: str=""; safety_note: str="不调用 xttrader、不真实下单、不查询真实账户、不真实通知。"
@dataclass
class RealCacheQualityReport:
    decision: RealCacheQualityDecision=RealCacheQualityDecision.NEED_MORE_EVIDENCE; safety_note: str="本阶段不是实盘授权，不下单，不调用 xttrader，不查询真实账户，不发送真实通知。"; evidence: list[RealCacheQualityEvidence]=field(default_factory=list); coverage: list[CacheCoverageItem]=field(default_factory=list); long_sample: list[LongSampleCompletenessItem]=field(default_factory=list); field_quality: list[FieldQualityItem]=field(default_factory=list); blocking_reasons: list[str]=field(default_factory=list); warnings: list[str]=field(default_factory=list); summary: dict[str, Any]=field(default_factory=dict)
@dataclass
class LongSampleGapFillReport: items: list[GapFillPlanItem]=field(default_factory=list); decision: RealCacheQualityDecision=RealCacheQualityDecision.NEED_MORE_EVIDENCE; safety_note: str="不调用 xttrader，不真实下单，不查询真实账户。"
@dataclass
class FieldQualityReviewReport: items: list[FieldQualityItem]=field(default_factory=list); decision: RealCacheQualityDecision=RealCacheQualityDecision.NEED_MORE_EVIDENCE; safety_note: str="字段复核只读/测试缓存，不代表实盘授权。"
@dataclass
class NextBacktestAttributionPlanReport: items: list[NextBacktestAttributionPlanItem]=field(default_factory=list); decision: RealCacheQualityDecision=RealCacheQualityDecision.NEED_MORE_EVIDENCE; safety_note: str="Stage57 仍不得直接实盘。"

def to_plain(obj: Any) -> Any:
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj, "__dataclass_fields__"): return {k: to_plain(v) for k,v in asdict(obj).items()}
    if isinstance(obj, list): return [to_plain(x) for x in obj]
    if isinstance(obj, dict): return {k: to_plain(v) for k,v in obj.items()}
    if isinstance(obj, Path): return str(obj)
    return obj
