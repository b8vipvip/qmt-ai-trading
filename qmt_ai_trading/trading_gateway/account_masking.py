from __future__ import annotations
from typing import Any

def mask_account_id(account_id: Any) -> str:
    s = "" if account_id is None else str(account_id)
    return "****" if len(s) < 6 else f"{s[:2]}****{s[-2:]}"

def mask_account_name(name: Any) -> str:
    s = "" if name is None else str(name)
    return "****" if len(s) < 6 else f"{s[:2]}****{s[-2:]}"

def mask_payload(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            lk = str(k).lower()
            if "account" in lk and ("id" in lk or "no" in lk or "name" in lk):
                out[k] = mask_account_name(v) if "name" in lk else mask_account_id(v)
            else:
                out[k] = mask_payload(v)
        return out
    if isinstance(obj, list):
        return [mask_payload(x) for x in obj]
    return obj
