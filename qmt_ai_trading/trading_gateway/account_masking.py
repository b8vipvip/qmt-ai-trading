from __future__ import annotations
from pathlib import Path
from typing import Any

SENSITIVE_KEYS = ("account", "acct", "fund", "client")
SENSITIVE_SUFFIXES = ("id", "no", "name", "code")


def mask_account_id(account_id: Any) -> str:
    s = "" if account_id is None else str(account_id)
    return "****" if len(s) < 6 else f"{s[:2]}****{s[-2:]}"


def mask_account_name(name: Any) -> str:
    s = "" if name is None else str(name)
    return "****" if len(s) < 6 else f"{s[:2]}****{s[-2:]}"


def _is_sensitive_key(key: Any) -> bool:
    lk = str(key).lower()
    return any(prefix in lk for prefix in SENSITIVE_KEYS) and any(suffix in lk for suffix in SENSITIVE_SUFFIXES)


def _public_object_fields(obj: Any) -> dict[str, Any]:
    """Convert xtquant return objects such as XtAsset/XtPosition into JSON-safe dicts."""
    if hasattr(obj, "_asdict"):
        try:
            return dict(obj._asdict())
        except Exception:
            pass
    if hasattr(obj, "to_dict"):
        try:
            value = obj.to_dict()
            if isinstance(value, dict):
                return value
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            raw = {k: v for k, v in vars(obj).items() if not str(k).startswith("_")}
            if raw:
                return raw
        except Exception:
            pass
    out: dict[str, Any] = {}
    for name in dir(obj):
        if name.startswith("_"):
            continue
        try:
            value = getattr(obj, name)
        except Exception:
            continue
        if callable(value):
            continue
        if isinstance(value, (str, int, float, bool, type(None))):
            out[name] = value
    if out:
        return out
    return {"value": str(obj), "object_type": obj.__class__.__name__}


def mask_payload(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if _is_sensitive_key(k):
                out[k] = mask_account_name(v) if "name" in str(k).lower() else mask_account_id(v)
            else:
                out[k] = mask_payload(v)
        return out
    if isinstance(obj, (list, tuple, set)):
        return [mask_payload(x) for x in obj]
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return mask_payload(_public_object_fields(obj))
