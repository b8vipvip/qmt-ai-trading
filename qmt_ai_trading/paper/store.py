"""Local JSON store for paper orders and execution reports."""

from __future__ import annotations

import json
from dataclasses import asdict, fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .models import PaperExecutionReport, PaperOrder, PaperOrderStatus


def json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: json_safe(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "__dict__"):
        return json_safe(vars(value))
    return value


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise FileNotFoundError(f"Paper trading file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Paper trading file is not valid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Paper trading file must contain a JSON object: {path}")
    return data


def _status(value: PaperOrderStatus | str | None) -> str | None:
    if value is None:
        return None
    return value.value if isinstance(value, PaperOrderStatus) else str(value)


class PaperOrderStore:
    def __init__(self, root_dir: str | Path = "paper_orders") -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get_order_path(self, paper_order_id: str) -> Path:
        return self.root_dir / f"paper_order_{paper_order_id}.json"

    def get_report_path(self, report_id: str) -> Path:
        return self.root_dir / f"paper_report_{report_id}.json"

    def save_order(self, order: PaperOrder) -> Path:
        path = self.get_order_path(order.paper_order_id)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(json_safe(order), fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        return path

    def load_order(self, paper_order_id: str) -> PaperOrder:
        data = _read_json(self.get_order_path(paper_order_id))
        allowed = {f.name for f in fields(PaperOrder)}
        return PaperOrder(**{k: v for k, v in data.items() if k in allowed})

    def list_orders(self, status: PaperOrderStatus | str | None = None, approval_id: str | None = None, symbol: str | None = None) -> list[PaperOrder]:
        expected = _status(status)
        orders = []
        for path in sorted(self.root_dir.glob("paper_order_*.json")):
            oid = path.stem[len("paper_order_"):]
            order = self.load_order(oid)
            if expected is not None and _status(order.status) != expected:
                continue
            if approval_id is not None and order.approval_id != approval_id:
                continue
            if symbol is not None and order.symbol != symbol:
                continue
            orders.append(order)
        return orders

    def save_report(self, report: PaperExecutionReport) -> Path:
        path = self.get_report_path(report.report_id)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(json_safe(report), fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        return path

    def load_report(self, report_id: str) -> PaperExecutionReport:
        data = _read_json(self.get_report_path(report_id))
        allowed = {f.name for f in fields(PaperExecutionReport)}
        return PaperExecutionReport(**{k: v for k, v in data.items() if k in allowed})

    def update_order_status(self, paper_order_id: str, status: PaperOrderStatus | str, **kwargs: Any) -> PaperOrder:
        order = self.load_order(paper_order_id)
        order.status = _status(status) or str(status)
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
        self.save_order(order)
        return order
