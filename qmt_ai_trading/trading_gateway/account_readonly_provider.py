from __future__ import annotations
from typing import Any
from .account_readonly_config import AccountReadonlyConfig
from .account_masking import mask_payload
from .account_rate_limit import AccountReadonlyRateLimiter

class AccountReadonlyProvider:
    def __init__(self, config: AccountReadonlyConfig | None = None, trader: Any = None, account: Any = None, rate_limiter: AccountReadonlyRateLimiter | None = None):
        self.config = config or AccountReadonlyConfig()
        self.trader = trader
        self.account = account
        self.rate_limiter = rate_limiter or AccountReadonlyRateLimiter(self.config.max_queries_per_minute)
    def get_status(self) -> dict:
        enabled = bool(self.config.enabled and self.config.read_only and self.config.manual_confirmation_completed)
        return {"status":"MANUAL_CONFIRM_REQUIRED" if self.config.enabled and not self.config.manual_confirmation_completed else ("SUCCESS" if enabled else "DISABLED"),"enabled":self.config.enabled,"account_query_enabled":enabled and self.config.allow_account_query,"position_query_enabled":enabled and self.config.allow_position_query,"order_submit_enabled":False,"order_cancel_enabled":False,"real_order_submitted":False,"safety_status":"MANUAL_CONFIRM_REQUIRED" if self.config.enabled and not self.config.manual_confirmation_completed else ("READONLY_ENABLED" if enabled else "DISABLED_FOR_SAFETY"),"mock_data":not enabled,"read_only":True,"requires_human_approval":True,"account_masked":True}
    def _blocked(self, gate: str) -> dict:
        return {**self.get_status(), "gate": gate, "query_attempted": False, "message": "account readonly query disabled by safety gate"}
    def _ensure_real_import(self) -> None:
        if self.trader is None and self.config.allow_import_xttrader:
            import importlib
            importlib.import_module("xtquant.xttrader")
    def query_account_asset(self) -> dict:
        if not (self.config.enabled and self.config.read_only and self.config.manual_confirmation_completed and self.config.allow_account_query):
            return self._blocked("account_asset")
        limited = self.rate_limiter.allow()
        if limited["status"] != "PASS":
            return limited
        if self.trader is None:
            return {"status":"SUCCESS","mock_data":True,"read_only":True,"account_masked":True,"asset":{"account_id":"91****91","cash":0.0,"total_asset":0.0},"order_submit_enabled":False,"real_order_submitted":False,"no_order_submitted":True}
        self._ensure_real_import()
        fn = getattr(self.trader, "query_stock_asset", None) or getattr(self.trader, "query_asset", None)
        data = fn(self.account) if self.account is not None else fn()
        return {"status":"SUCCESS","mock_data":False,"read_only":True,"account_masked":True,"asset":mask_payload(data),"order_submit_enabled":False,"real_order_submitted":False,"no_order_submitted":True}
    def query_positions(self) -> dict:
        if not (self.config.enabled and self.config.read_only and self.config.manual_confirmation_completed and self.config.allow_position_query):
            return self._blocked("positions")
        limited = self.rate_limiter.allow()
        if limited["status"] != "PASS":
            return limited
        if self.trader is None:
            positions=[{"account_id":"91****91","symbol":"159915.SZ","volume":0,"available_volume":0}]
            return {"status":"SUCCESS","mock_data":True,"read_only":True,"account_masked":True,"positions":positions,"position_count":len(positions),"order_submit_enabled":False,"real_order_submitted":False,"no_order_submitted":True}
        self._ensure_real_import()
        fn = getattr(self.trader, "query_stock_positions", None) or getattr(self.trader, "query_positions", None)
        data = fn(self.account) if self.account is not None else fn()
        data = data if isinstance(data, list) else list(data or [])
        return {"status":"SUCCESS","mock_data":False,"read_only":True,"account_masked":True,"positions":mask_payload(data),"position_count":len(data),"order_submit_enabled":False,"real_order_submitted":False,"no_order_submitted":True}
