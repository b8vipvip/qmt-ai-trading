"""Local JSON file store for human approval requests and decisions."""

from __future__ import annotations

import json
from dataclasses import asdict, fields, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from .models import ApprovalDecision, ApprovalRequest, ApprovalStatus


def _json_safe(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {k: _json_safe(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return value


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise FileNotFoundError(f"Approval file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Approval file is not valid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Approval file must contain a JSON object: {path}")
    return data


def _coerce_status(status: ApprovalStatus | str) -> str:
    return status.value if isinstance(status, ApprovalStatus) else str(status)


class ApprovalStore:
    def __init__(self, root_dir: str | Path = "approvals") -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def get_request_path(self, approval_id: str) -> Path:
        return self.root_dir / f"approval_{approval_id}.json"

    def get_decision_path(self, approval_id: str) -> Path:
        return self.root_dir / f"approval_{approval_id}.decision.json"

    def save_request(self, request: ApprovalRequest) -> Path:
        path = self.get_request_path(request.approval_id)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(_json_safe(request), fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        return path

    def load_request(self, approval_id: str) -> ApprovalRequest:
        data = _read_json(self.get_request_path(approval_id))
        allowed = {f.name for f in fields(ApprovalRequest)}
        return ApprovalRequest(**{k: v for k, v in data.items() if k in allowed})

    def list_requests(self, status: ApprovalStatus | str | None = None) -> list[ApprovalRequest]:
        expected = _coerce_status(status) if status is not None else None
        requests: list[ApprovalRequest] = []
        for path in sorted(self.root_dir.glob("approval_*.json")):
            if path.name.endswith(".decision.json"):
                continue
            stem = path.stem
            if stem.startswith("approval_"):
                approval_id = stem[len("approval_"):]
            else:
                approval_id = stem
            req = self.load_request(approval_id)
            if expected is None or _coerce_status(req.status) == expected:
                requests.append(req)
        return requests

    def save_decision(self, decision: ApprovalDecision) -> Path:
        path = self.get_decision_path(decision.approval_id)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(_json_safe(decision), fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        return path

    def load_decision(self, approval_id: str) -> ApprovalDecision:
        data = _read_json(self.get_decision_path(approval_id))
        allowed = {f.name for f in fields(ApprovalDecision)}
        return ApprovalDecision(**{k: v for k, v in data.items() if k in allowed})

    def update_status(self, approval_id: str, status: ApprovalStatus | str, decision: ApprovalDecision | None = None) -> ApprovalRequest:
        req = self.load_request(approval_id)
        req.status = _coerce_status(status)
        self.save_request(req)
        if decision is not None:
            self.save_decision(decision)
        return req

    def mark_expired(self, now: datetime | str | None = None) -> list[ApprovalRequest]:
        current = now if isinstance(now, datetime) else datetime.fromisoformat(now) if isinstance(now, str) else datetime.now(timezone.utc)
        expired: list[ApprovalRequest] = []
        for req in self.list_requests(ApprovalStatus.PENDING):
            expires = datetime.fromisoformat(str(req.expires_at).replace("Z", "+00:00"))
            if expires <= current:
                req.status = ApprovalStatus.EXPIRED.value
                self.save_request(req)
                expired.append(req)
        return expired
