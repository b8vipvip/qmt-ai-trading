"""Diagnostics and field calibration helpers for QMT historical xtdata."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.qmt_field_mapping import QMT_OPTIONAL_BAR_FIELDS, QMT_REQUIRED_BAR_FIELDS, map_qmt_record_fields
from qmt_ai_trading.datahub.qmt_provider import normalize_qmt_raw_records


@dataclass
class QmtRuntimeInfo:
    xtdata_available: bool
    xtdata_module_path: str | None = None
    has_connect: bool = False
    connect_success: bool | None = None
    connect_message: str = ""
    supported_functions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QmtSampleFetchResult:
    success: bool
    symbol: str
    frequency: str
    start_date: str
    end_date: str
    row_count: int = 0
    raw_type: str = ""
    raw_columns: list[str] = field(default_factory=list)
    normalized_count: int = 0
    cache_path: str = ""
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QmtFieldCalibration:
    raw_columns: list[str] = field(default_factory=list)
    mapped_fields: dict[str, str] = field(default_factory=dict)
    missing_required_fields: list[str] = field(default_factory=list)
    optional_fields: list[str] = field(default_factory=list)
    frequency: str = "1d"
    sample_rows: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QmtDataQualityReport:
    symbol: str
    frequency: str
    start_date: str
    end_date: str
    row_count: int = 0
    first_datetime: str | None = None
    last_datetime: str | None = None
    missing_ohlc_count: int = 0
    zero_volume_count: int = 0
    duplicate_datetime_count: int = 0
    sorted_by_datetime: bool = True
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _import_xtdata_safe() -> tuple[bool, Any, str]:
    try:
        from xtquant import xtdata  # type: ignore
    except Exception as exc:  # pragma: no cover
        return False, None, str(exc)
    return True, xtdata, "import ok"


def inspect_qmt_runtime(try_connect: bool = False, xtdata_module: Any = None) -> QmtRuntimeInfo:
    available = xtdata_module is not None
    message = "injected xtdata module" if available else ""
    xtdata = xtdata_module
    if xtdata is None:
        available, xtdata, message = _import_xtdata_safe()
    if not available:
        return QmtRuntimeInfo(False, connect_message=f"xtquant.xtdata unavailable: {message}", metadata={"trading_api_used": False})
    funcs = sorted(name for name in dir(xtdata) if not name.startswith("_") and callable(getattr(xtdata, name, None)))
    connect = getattr(xtdata, "connect", None)
    info = QmtRuntimeInfo(True, getattr(xtdata, "__file__", None), callable(connect), supported_functions=funcs, connect_message="connect not attempted", metadata={"trading_api_used": False})
    if try_connect and callable(connect):
        try:
            result = connect()
            info.connect_success = True if result is None else bool(result)
            info.connect_message = f"xtdata.connect() returned {result!r}"
        except Exception as exc:  # pragma: no cover
            info.connect_success = False
            info.connect_message = f"xtdata.connect() failed: {exc}"
    elif try_connect:
        info.connect_success = True
        info.connect_message = "xtdata.connect() not available; import succeeded"
    return info


def _records(raw_data: Any) -> list[Mapping[str, Any]]:
    if raw_data is None:
        return []
    if hasattr(raw_data, "to_dict"):
        try:
            rows = raw_data.to_dict("records")
            return [r for r in rows if isinstance(r, Mapping)]
        except Exception:
            pass
    if isinstance(raw_data, list):
        return [r for r in raw_data if isinstance(r, Mapping)]
    if isinstance(raw_data, Mapping):
        if any(isinstance(v, (list, tuple)) for v in raw_data.values()):
            n = max((len(v) for v in raw_data.values() if isinstance(v, (list, tuple))), default=0)
            return [{k: (v[i] if isinstance(v, (list, tuple)) and i < len(v) else v) for k, v in raw_data.items()} for i in range(n)]
        return [raw_data]
    return []


def inspect_qmt_raw_schema(raw_data: Any) -> QmtFieldCalibration:
    return calibrate_qmt_bar_fields(raw_data)


def calibrate_qmt_bar_fields(raw_data: Any, frequency: str = "1d") -> QmtFieldCalibration:
    rows = _records(raw_data)
    columns = sorted({str(k) for row in rows for k in row.keys()})
    mapped: dict[str, str] = {}
    if rows:
        first = rows[0]
        canonical = map_qmt_record_fields(first)
        for field in canonical:
            for raw_key in first.keys():
                if map_qmt_record_fields({raw_key: first[raw_key]}).get(field) is not None:
                    mapped[field] = str(raw_key)
                    break
    missing = [f for f in QMT_REQUIRED_BAR_FIELDS if f not in mapped]
    optional = [f for f in QMT_OPTIONAL_BAR_FIELDS if f in mapped]
    msg = "schema recognized" if not missing else f"missing required fields: {missing}"
    return QmtFieldCalibration(columns, mapped, missing, optional, frequency, [dict(r) for r in rows[:3]], msg, {"raw_type": type(raw_data).__name__})


def build_qmt_data_quality_report(bars: list[MarketBar], symbol: str, frequency: str, start_date: str, end_date: str) -> QmtDataQualityReport:
    datetimes = [str(b.datetime) for b in bars if b.datetime is not None]
    seen: set[str] = set(); dup = 0
    for dt in datetimes:
        if dt in seen: dup += 1
        seen.add(dt)
    missing = sum(1 for b in bars if b.open is None or b.high is None or b.low is None or b.close is None)
    zero_vol = sum(1 for b in bars if b.volume in (0, 0.0))
    sorted_ok = datetimes == sorted(datetimes)
    return QmtDataQualityReport(symbol, frequency, start_date, end_date, len(bars), datetimes[0] if datetimes else None, datetimes[-1] if datetimes else None, missing, zero_vol, dup, sorted_ok, "quality check completed")


def format_qmt_runtime_info(info: QmtRuntimeInfo) -> str:
    return "\n".join([
        "QMT Runtime Info",
        f"xtdata_available={info.xtdata_available}",
        f"xtdata_module_path={info.xtdata_module_path or 'n/a'}",
        f"has_connect={info.has_connect}",
        f"connect_success={info.connect_success}",
        f"connect_message={info.connect_message}",
        f"supported_functions_count={len(info.supported_functions)}",
        "trading APIs: not used; xttrader is not imported",
    ])


def format_qmt_sample_result(result: QmtSampleFetchResult) -> str:
    return "\n".join(f"{k}={v}" for k, v in asdict(result).items())


def format_qmt_data_quality_report(report: QmtDataQualityReport) -> str:
    return "\n".join([
        "QMT Data Quality Report",
        f"symbol={report.symbol}", f"frequency={report.frequency}", f"row_count={report.row_count}",
        f"first_datetime={report.first_datetime}", f"last_datetime={report.last_datetime}",
        f"missing_ohlc_count={report.missing_ohlc_count}", f"zero_volume_count={report.zero_volume_count}",
        f"duplicate_datetime_count={report.duplicate_datetime_count}", f"sorted_by_datetime={report.sorted_by_datetime}", f"message={report.message}",
    ])
