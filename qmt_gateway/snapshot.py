# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
from .safety import redact_account_id

def _value(obj, name, default=0):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

def normalize_asset(asset):
    return {"total_asset": float(_value(asset, "total_asset", 0) or 0), "cash": float(_value(asset, "cash", 0) or 0)}

def normalize_position(pos):
    return {"stock_code": _value(pos, "stock_code", ""), "volume": int(_value(pos, "volume", 0) or 0),
            "can_use_volume": int(_value(pos, "can_use_volume", _value(pos, "volume", 0)) or 0)}

def build_account_snapshot(account_id=None, asset=None, positions=None, errors=None, warnings=None):
    return {"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "mode": "READ_ONLY",
            "account_id_masked": redact_account_id(account_id), "asset": normalize_asset(asset or {}),
            "positions": [normalize_position(p) for p in (positions or [])], "errors": errors or [], "warnings": warnings or []}
