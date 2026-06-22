from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from math import isinf, isnan
from typing import Any


def json_safe(value: Any) -> Any:
    """Convert common third-party Python objects into JSON-serializable values."""
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return None if isnan(value) or isinf(value) else value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    try:
        import pandas as pd  # type: ignore
        if isinstance(value, pd.DataFrame):
            df = value.copy()
            try:
                df = df.reset_index()
            except Exception:
                pass
            try:
                df.columns = [str(c) for c in df.columns]
            except Exception:
                pass
            return json_safe(df.to_dict(orient="records"))
        if isinstance(value, pd.Series):
            return json_safe(value.to_dict())
        if isinstance(value, pd.Timestamp):
            return value.isoformat()
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
    except Exception:
        pass

    try:
        import numpy as np  # type: ignore
        if isinstance(value, np.generic):
            return json_safe(value.item())
        if isinstance(value, np.ndarray):
            return json_safe(value.tolist())
    except Exception:
        pass

    if is_dataclass(value) and not isinstance(value, type):
        return json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    if hasattr(value, "to_dict"):
        try:
            return json_safe(value.to_dict())
        except Exception:
            pass
    if hasattr(value, "tolist"):
        try:
            return json_safe(value.tolist())
        except Exception:
            pass
    return repr(value)
