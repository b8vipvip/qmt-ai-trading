"""Stage 24 QMT real-data cache quality checks.

This module is dependency-light and never imports xttrader. It only evaluates
already-normalized market bars and LocalBarStore cache roundtrips.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

from qmt_ai_trading.datahub.local_store import BarCacheResult, BarQuery, LocalBarStore
from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.symbols import normalize_symbol


class QmtDataAvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class QmtCacheQualityStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass
class QmtDataQualityCheck:
    check_id: str
    name: str
    status: QmtCacheQualityStatus | str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QmtDataQualityReport:
    report_id: str
    created_at: str
    symbol: str
    frequency: str
    start_date: str
    end_date: str
    provider: str
    xtdata_available: QmtDataAvailabilityStatus | str
    qmt_available: QmtDataAvailabilityStatus | str
    cache_root: str
    raw_row_count: int
    normalized_bar_count: int
    cache_hit_after_save: bool
    first_datetime: str | None
    last_datetime: str | None
    duplicate_datetime_count: int
    missing_ohlc_count: int
    zero_volume_count: int
    sorted_by_datetime: bool
    checks: list[QmtDataQualityCheck] = field(default_factory=list)
    decision: QmtCacheQualityStatus | str = QmtCacheQualityStatus.SKIP
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _value(obj: Any, name: str) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name)
    return getattr(obj, name, None)


def _iso_dt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _extract_bars(data: Any) -> list[Any]:
    if data is None:
        return []
    if isinstance(data, BarCacheResult):
        return list(data.bars)
    if hasattr(data, "bars"):
        return list(getattr(data, "bars") or [])
    if isinstance(data, Iterable) and not isinstance(data, (str, bytes, Mapping)):
        return list(data)
    return []


def _check(check_id: str, name: str, ok: bool, fail_status: QmtCacheQualityStatus, message_ok: str, message_bad: str, evidence: dict[str, Any]) -> QmtDataQualityCheck:
    return QmtDataQualityCheck(check_id, name, QmtCacheQualityStatus.PASS if ok else fail_status, message_ok if ok else message_bad, evidence)


def check_qmt_bar_quality(bars_or_dataset: Any, *, min_bars: int = 1) -> tuple[list[QmtDataQualityCheck], dict[str, Any]]:
    bars = _extract_bars(bars_or_dataset)
    datetimes = [_iso_dt(_value(bar, "datetime")) for bar in bars]
    seen: set[str] = set()
    duplicate_count = 0
    for item in datetimes:
        if item in seen:
            duplicate_count += 1
        seen.add(item)
    missing_ohlc = sum(1 for bar in bars if any(_value(bar, f) is None for f in ("open", "high", "low", "close")))
    zero_volume = sum(1 for bar in bars if _value(bar, "volume") in (0, 0.0))
    sorted_ok = datetimes == sorted(datetimes)
    summary = {
        "bar_count": len(bars),
        "first_datetime": datetimes[0] if datetimes else None,
        "last_datetime": datetimes[-1] if datetimes else None,
        "duplicate_datetime_count": duplicate_count,
        "missing_ohlc_count": missing_ohlc,
        "zero_volume_count": zero_volume,
        "sorted_by_datetime": sorted_ok,
    }
    checks = [
        _check("bar_count", "Bar count", len(bars) >= min_bars, QmtCacheQualityStatus.WARN, "bar count meets minimum", "bar count below minimum", {"bar_count": len(bars), "min_bars": min_bars}),
        _check("duplicate_datetime", "Duplicate datetime", duplicate_count == 0, QmtCacheQualityStatus.FAIL, "no duplicate datetime", "duplicate datetime detected", {"duplicate_datetime_count": duplicate_count}),
        _check("missing_ohlc", "Missing OHLC", missing_ohlc == 0, QmtCacheQualityStatus.FAIL, "OHLC fields complete", "missing OHLC fields detected", {"missing_ohlc_count": missing_ohlc}),
        _check("zero_volume", "Zero volume", zero_volume == 0, QmtCacheQualityStatus.WARN, "no zero volume bars", "zero volume bars detected", {"zero_volume_count": zero_volume}),
        _check("datetime_sorted", "Datetime sorted", sorted_ok, QmtCacheQualityStatus.FAIL, "bars sorted by datetime", "bars are not sorted by datetime", {"sorted_by_datetime": sorted_ok}),
    ]
    return checks, summary


def _coerce_market_bars(bars: Any, symbol: str) -> list[MarketBar]:
    result: list[MarketBar] = []
    for bar in _extract_bars(bars):
        if isinstance(bar, MarketBar):
            result.append(bar)
        elif is_dataclass(bar):
            data = asdict(bar)
            result.append(MarketBar(normalize_symbol(str(data.get("symbol") or symbol)), data.get("datetime"), data.get("open"), data.get("high"), data.get("low"), data.get("close"), data.get("volume"), data.get("amount"), str(data.get("source") or "qmt")))
        elif isinstance(bar, Mapping):
            result.append(MarketBar(normalize_symbol(str(bar.get("symbol") or symbol)), bar.get("datetime") or bar.get("date") or bar.get("time"), bar.get("open"), bar.get("high"), bar.get("low"), bar.get("close"), bar.get("volume"), bar.get("amount"), str(bar.get("source") or "qmt")))
    return result


def check_cache_roundtrip(store: LocalBarStore, *, symbol: str, frequency: str, start_date: str, end_date: str, bars: Any | None = None, provider: str = "qmt") -> tuple[bool, list[MarketBar], str]:
    if bars is not None:
        normalized = _coerce_market_bars(bars, symbol)
        if normalized:
            store.save_bars(symbol, frequency, normalized, provider=provider)
    query = BarQuery([symbol], start_date, end_date, frequency=frequency, provider="local")
    result = store.query_bars(query)
    return bool(result.hit and result.bars), list(result.bars), result.message


def build_qmt_quality_report(*, symbol: str, frequency: str, start_date: str, end_date: str, provider: str = "qmt", cache_root: str | Path = "market_data_qmt_stage24", bars: Any = None, raw_row_count: int | None = None, xtdata_available: QmtDataAvailabilityStatus | str = QmtDataAvailabilityStatus.SKIPPED, qmt_available: QmtDataAvailabilityStatus | str = QmtDataAvailabilityStatus.SKIPPED, cache_hit_after_save: bool = False, checks: list[QmtDataQualityCheck] | None = None, message: str = "", metadata: dict[str, Any] | None = None, min_bars: int = 1) -> QmtDataQualityReport:
    quality_checks, summary = check_qmt_bar_quality(bars, min_bars=min_bars)
    all_checks = list(checks or []) + quality_checks
    statuses = [str(c.status.value if isinstance(c.status, Enum) else c.status) for c in all_checks]
    if any(s == QmtCacheQualityStatus.FAIL.value for s in statuses):
        decision = QmtCacheQualityStatus.FAIL
    elif not _extract_bars(bars) or any(s == QmtCacheQualityStatus.SKIP.value for s in statuses):
        decision = QmtCacheQualityStatus.SKIP
    elif any(s == QmtCacheQualityStatus.WARN.value for s in statuses) or not cache_hit_after_save:
        decision = QmtCacheQualityStatus.WARN
    else:
        decision = QmtCacheQualityStatus.PASS
    return QmtDataQualityReport(
        report_id=f"qmt_quality_{normalize_symbol(symbol).replace('.', '_')}_{frequency}_{_now_iso().replace(':', '').replace('+', 'Z')}",
        created_at=_now_iso(), symbol=normalize_symbol(symbol), frequency=frequency, start_date=start_date, end_date=end_date, provider=provider,
        xtdata_available=xtdata_available, qmt_available=qmt_available, cache_root=str(cache_root), raw_row_count=raw_row_count if raw_row_count is not None else len(_extract_bars(bars)),
        normalized_bar_count=int(summary["bar_count"]), cache_hit_after_save=cache_hit_after_save, first_datetime=summary["first_datetime"], last_datetime=summary["last_datetime"],
        duplicate_datetime_count=int(summary["duplicate_datetime_count"]), missing_ohlc_count=int(summary["missing_ohlc_count"]), zero_volume_count=int(summary["zero_volume_count"]), sorted_by_datetime=bool(summary["sorted_by_datetime"]),
        checks=all_checks, decision=decision, message=message or f"QMT cache quality decision: {decision.value}", metadata=dict(metadata or {}),
    )


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value


def format_qmt_quality_report_json(report: QmtDataQualityReport) -> str:
    return json.dumps(_jsonable(report), ensure_ascii=False, indent=2, sort_keys=True)


def format_qmt_quality_report_markdown(report: QmtDataQualityReport) -> str:
    lines = [
        f"# QMT Data Quality Report - {report.symbol}", "",
        f"- decision: {report.decision.value if isinstance(report.decision, Enum) else report.decision}",
        f"- symbol: {report.symbol}", f"- frequency: {report.frequency}", f"- date_range: {report.start_date} to {report.end_date}", f"- provider: {report.provider}",
        f"- xtdata_available: {report.xtdata_available.value if isinstance(report.xtdata_available, Enum) else report.xtdata_available}",
        f"- qmt_available: {report.qmt_available.value if isinstance(report.qmt_available, Enum) else report.qmt_available}", f"- cache_root: {report.cache_root}",
        f"- raw_row_count: {report.raw_row_count}", f"- normalized_bar_count: {report.normalized_bar_count}", f"- cache_hit_after_save: {report.cache_hit_after_save}",
        f"- first_datetime: {report.first_datetime}", f"- last_datetime: {report.last_datetime}", f"- duplicate_datetime_count: {report.duplicate_datetime_count}",
        f"- missing_ohlc_count: {report.missing_ohlc_count}", f"- zero_volume_count: {report.zero_volume_count}", f"- sorted_by_datetime: {report.sorted_by_datetime}", "", "## Checks", "",
        "| check_id | status | message |", "|---|---:|---|",
    ]
    for check in report.checks:
        status = check.status.value if isinstance(check.status, Enum) else check.status
        lines.append(f"| {check.check_id} | {status} | {check.message} |")
    lines += ["", "## Safety", "", "This report is market-data quality evidence only. It is not trading approval; xttrader and order/trade interfaces are not used."]
    return "\n".join(lines) + "\n"
