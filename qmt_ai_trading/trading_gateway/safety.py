from __future__ import annotations
from pathlib import Path
from .models import XtTraderBoundaryConfig

DANGEROUS_MARKERS = ["XtQuant"+"Trader(", "query_"+"account", "query_"+"position", "query_"+"order", "query_"+"trade", "query_stock_"+"asset", "query_stock_"+"positions", "query_stock_"+"orders", "query_stock_"+"trades", "order_"+"stock", "order_stock_"+"async", "cancel_order_"+"stock", "cancel_order_stock_"+"async", "place_"+"order", "execute_"+"order", "real_order_submitted=true", "allow_order_submit=true", "allow_account_query=true", "allow_import_xttrader=true"]

def validate_config(config: XtTraderBoundaryConfig) -> dict:
    cfg = config.to_dict()
    bad = [k for k, v in cfg.items() if k.startswith("allow_") and v is True] + (["enabled"] if cfg.get("enabled") else [])
    return {"status":"PASS" if not bad else "BLOCKED_BY_SAFETY", "unsafe_fields":bad, "safety_status":"DISABLED_FOR_SAFETY", "enabled":False, "dry_run":True, "read_only":True, "real_order_submitted":False}

def scan_text(paths: list[str], repo_root: str = ".") -> dict:
    hits=[]; root=Path(repo_root)
    for p in paths:
        path=root/p
        if path.exists():
            text=path.read_text(encoding="utf-8", errors="ignore")
            low=text.lower().replace(' ', '')
            for m in DANGEROUS_MARKERS:
                if m.lower().replace(' ', '') in low:
                    hits.append({"file":p,"marker":m})
    return {"status":"PASS" if not hits else "FAIL", "hits":hits, "safety_status":"DISABLED_FOR_SAFETY", "xttrader_imported":False, "real_order_submitted":False}
