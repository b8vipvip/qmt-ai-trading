from __future__ import annotations
from typing import Any
FORBIDDEN=("xttrader","query_stock_asset","query_stock_positions","query_stock_orders","query_stock_trades","place_order","submit_order","order_stock","buy(","sell(","cancel_order")
SENSITIVE=("token","key","password","secret","account")
def contains_forbidden_trading_access(text: str) -> bool:
    t=(text or "").lower(); return any(x in t for x in FORBIDDEN)
def assert_no_xttrader_import() -> None:
    import sys
    if any("xttrader" in k.lower() for k in sys.modules): raise RuntimeError("xttrader import is forbidden for data quality tracking")
def validate_data_quality_tracking_is_read_only() -> bool:
    assert_no_xttrader_import(); return True
def sanitize_data_quality_metadata(metadata: Any) -> Any:
    if isinstance(metadata, dict):
        return {str(k): ("***REDACTED***" if any(s in str(k).lower() for s in SENSITIVE) else sanitize_data_quality_metadata(v)) for k,v in metadata.items()}
    if isinstance(metadata, list): return [sanitize_data_quality_metadata(x) for x in metadata]
    if isinstance(metadata, str) and contains_forbidden_trading_access(metadata): return "***REDACTED_FORBIDDEN_TRADING_ACCESS***"
    return metadata
def validate_no_trading_side_effect(report: Any) -> bool:
    text=str(report.to_dict() if hasattr(report,"to_dict") else report)
    if contains_forbidden_trading_access(text): raise RuntimeError("forbidden trading access text detected")
    return True
