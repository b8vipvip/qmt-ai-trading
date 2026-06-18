from __future__ import annotations
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SAFETY_NOTE = "Data quality tracking is read-only. It does not query accounts, positions, orders, trades, or submit orders."

def now_iso() -> str: return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
class DataQualityLevel(str, Enum):
    PASS="PASS"; WARN="WARN"; FAIL="FAIL"; UNKNOWN="UNKNOWN"; UNAVAILABLE="UNAVAILABLE"; SKIPPED="SKIPPED"

def _clean(v: Any) -> Any:
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {k: _clean(x) for k,x in asdict(v).items()}
    if isinstance(v, list): return [_clean(x) for x in v]
    if isinstance(v, dict): return {str(k): _clean(x) for k,x in v.items()}
    return v

@dataclass
class JsonModel:
    def to_dict(self) -> dict[str, Any]: return _clean(self)

@dataclass
class DataQualityMetric(JsonModel):
    metric_id: str; symbol: str=""; trade_date: str=""; metric_name: str=""; value: Any=None; threshold: Any=None; level: DataQualityLevel|str=DataQualityLevel.UNKNOWN; message: str=""; metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class DataQualityLedgerEntry(JsonModel):
    entry_id: str; created_at: str=field(default_factory=now_iso); source: str=""; symbol: str=""; trade_date: str=""; quality_level: DataQualityLevel|str=DataQualityLevel.UNKNOWN; coverage_ratio: float=0.0; loaded_bars: int=0; expected_bars: int=0; missing_bars: int=0; duplicate_bars: int=0; anomaly_count: int=0; field_missing_count: int=0; source_report_path: str=""; metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class DataQualityTrend(JsonModel):
    trend_id: str; symbol: str=""; start_date: str=""; end_date: str=""; observations: int=0; pass_count: int=0; warn_count: int=0; fail_count: int=0; unknown_count: int=0; unavailable_count: int=0; average_coverage: float=0.0; max_missing_bars: int=0; max_anomaly_count: int=0; trend_level: DataQualityLevel|str=DataQualityLevel.UNKNOWN; message: str=""; metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class DataQualityIncident(JsonModel):
    incident_id: str; created_at: str=field(default_factory=now_iso); symbol: str=""; category: str=""; severity: str="WARNING"; title: str=""; message: str=""; first_seen: str=""; last_seen: str=""; evidence: list[dict[str,Any]]=field(default_factory=list); remediation: str=""; metadata: dict[str,Any]=field(default_factory=dict)
@dataclass
class DataQualityTrackingReport(JsonModel):
    report_id: str; created_at: str=field(default_factory=now_iso); source: str=""; start_date: str=""; end_date: str=""; ledger_entries: list[DataQualityLedgerEntry]=field(default_factory=list); trends: list[DataQualityTrend]=field(default_factory=list); incidents: list[DataQualityIncident]=field(default_factory=list); summary: dict[str,Any]=field(default_factory=dict); success: bool=True; message: str=""; safety_note: str=SAFETY_NOTE; metadata: dict[str,Any]=field(default_factory=dict)
