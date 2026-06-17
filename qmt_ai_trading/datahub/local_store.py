"""Local historical bar cache for Data Hub.

The store is intentionally dependency-light: JSONL data files plus a small JSON
metadata index per symbol/frequency. It does not call QMT or any external API.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from qmt_ai_trading.datahub.models import MarketBar
from qmt_ai_trading.datahub.symbols import normalize_symbol


@dataclass
class BarQuery:
    symbols: list[str]
    start_date: date | datetime | str
    end_date: date | datetime | str
    frequency: str = "1d"
    adjust: str | None = None
    provider: str = "local"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BarCacheMetadata:
    symbol: str
    frequency: str
    start_date: str
    end_date: str
    row_count: int
    path: str
    provider: str = "local"
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BarCacheResult:
    query: BarQuery
    hit: bool
    missing_ranges: list[tuple[str, str]] = field(default_factory=list)
    bars: list[MarketBar] = field(default_factory=list)
    metadata: list[BarCacheMetadata] = field(default_factory=list)
    message: str = ""


def _iso_day(value: date | datetime | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if "T" in text:
        text = text.split("T", 1)[0]
    if " " in text:
        text = text.split(" ", 1)[0]
    return text


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _bar_date(bar: MarketBar | Mapping[str, Any]) -> str:
    value = bar.datetime if isinstance(bar, MarketBar) else bar.get("datetime") or bar.get("date") or bar.get("time")
    return _iso_day(value)


def _bar_to_dict(bar: MarketBar | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(bar, MarketBar):
        data = asdict(bar)
    elif is_dataclass(bar):
        data = asdict(bar)  # type: ignore[arg-type]
    else:
        data = dict(bar)
    if isinstance(data.get("datetime"), (datetime, date)):
        data["datetime"] = data["datetime"].isoformat()
    return data


def _bar_from_dict(symbol: str, row: Mapping[str, Any]) -> MarketBar:
    return MarketBar(
        symbol=normalize_symbol(str(row.get("symbol") or symbol)),
        datetime=row.get("datetime") or row.get("date") or row.get("time"),
        open=_to_float(row.get("open")),
        high=_to_float(row.get("high")),
        low=_to_float(row.get("low")),
        close=_to_float(row.get("close")),
        volume=_to_float(row.get("volume")),
        amount=_to_float(row.get("amount")),
        source=str(row.get("source") or row.get("provider") or "local"),
    )


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class LocalBarStore:
    """JSONL-backed local historical bar store."""

    def __init__(self, root_dir: str | Path = "market_data") -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get_symbol_dir(self, symbol: str, frequency: str) -> Path:
        path = self.root_dir / normalize_symbol(symbol) / frequency
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_metadata_path(self, symbol: str, frequency: str) -> Path:
        return self.get_symbol_dir(symbol, frequency) / "metadata.json"

    def _bars_path(self, symbol: str, frequency: str) -> Path:
        return self.get_symbol_dir(symbol, frequency) / f"{normalize_symbol(symbol)}.{frequency}.bars.jsonl"

    def load_metadata(self, symbol: str, frequency: str) -> BarCacheMetadata | None:
        path = self.get_metadata_path(symbol, frequency)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return BarCacheMetadata(**data)
        except (OSError, json.JSONDecodeError, TypeError):
            return None

    def save_metadata(self, metadata: BarCacheMetadata) -> None:
        path = self.get_metadata_path(metadata.symbol, metadata.frequency)
        path.write_text(json.dumps(asdict(metadata), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def load_bars(self, query: BarQuery) -> list[MarketBar]:
        start, end = _iso_day(query.start_date), _iso_day(query.end_date)
        bars: list[MarketBar] = []
        for symbol in query.symbols:
            path = self._bars_path(symbol, query.frequency)
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    bar = _bar_from_dict(symbol, json.loads(line))
                except json.JSONDecodeError:
                    continue
                day = _bar_date(bar)
                if start <= day <= end:
                    bars.append(bar)
        return sorted(bars, key=lambda item: (item.symbol, _bar_date(item)))

    def save_bars(self, symbol: str, frequency: str, bars: Iterable[MarketBar | Mapping[str, Any]], provider: str = "local") -> BarCacheMetadata:
        normalized = normalize_symbol(symbol)
        path = self._bars_path(normalized, frequency)
        existing: dict[str, dict[str, Any]] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        row = json.loads(line)
                        existing[_bar_date(row)] = row
                    except json.JSONDecodeError:
                        continue
        for bar in bars:
            row = _bar_to_dict(bar)
            row["symbol"] = normalize_symbol(str(row.get("symbol") or normalized))
            row.setdefault("source", provider)
            day = _bar_date(row)
            if day:
                existing[day] = row
        ordered = [existing[key] for key in sorted(existing)]
        path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ordered), encoding="utf-8")
        now = _now_iso()
        old = self.load_metadata(normalized, frequency)
        dates = sorted(existing)
        metadata = BarCacheMetadata(
            symbol=normalized,
            frequency=frequency,
            start_date=dates[0] if dates else "",
            end_date=dates[-1] if dates else "",
            row_count=len(ordered),
            path=str(path),
            provider=provider,
            created_at=old.created_at if old else now,
            updated_at=now,
            metadata={"format": "jsonl"},
        )
        self.save_metadata(metadata)
        return metadata

    def query_bars(self, query: BarQuery) -> BarCacheResult:
        missing = self.find_missing_ranges(query)
        bars = self.load_bars(query) if not missing else []
        metadata = [m for symbol in query.symbols if (m := self.load_metadata(symbol, query.frequency))]
        return BarCacheResult(query=query, hit=not missing, missing_ranges=missing, bars=bars, metadata=metadata, message="cache hit" if not missing else "cache miss")

    def has_coverage(self, query: BarQuery) -> bool:
        return not self.find_missing_ranges(query)

    def find_missing_ranges(self, query: BarQuery) -> list[tuple[str, str]]:
        start, end = _iso_day(query.start_date), _iso_day(query.end_date)
        missing: list[tuple[str, str]] = []
        for symbol in query.symbols:
            meta = self.load_metadata(symbol, query.frequency)
            if not meta or not meta.start_date or not meta.end_date or meta.start_date > start or meta.end_date < end:
                missing.append((start, end))
        return missing

    def clear_symbol(self, symbol: str, frequency: str | None = None) -> None:
        base = self.root_dir / normalize_symbol(symbol)
        target = base / frequency if frequency else base
        if target.exists():
            shutil.rmtree(target)
