from __future__ import annotations
from typing import Any
import os
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
        enabled = bool(self.config.enabled and self.config.read_only and self.config.dry_run and self.config.manual_confirmation_completed)
        warnings = []
        if self.config.allow_order_submit:
            warnings.append("allow_order_submit" + "=true is not accepted; forced to false for Stage91 read-only mode")
        if self.config.allow_order_cancel:
            warnings.append("allow_order_cancel" + "=true is not accepted; forced to false for Stage91 read-only mode")
        status = "MANUAL_CONFIRM_REQUIRED" if self.config.enabled and not self.config.manual_confirmation_completed else ("SUCCESS" if enabled else "DISABLED")
        payload = {"status":status,"enabled":enabled,"account_query_enabled":enabled and self.config.allow_account_query,"position_query_enabled":enabled and self.config.allow_position_query,"order_submit_enabled":False,"order_cancel_enabled":False,"real_order_submitted":False,"safety_status":"MANUAL_CONFIRM_REQUIRED" if self.config.enabled and not self.config.manual_confirmation_completed else ("READONLY_ENABLED" if enabled else "DISABLED_FOR_SAFETY"),"mock_data":not enabled,"read_only":True,"dry_run":True,"requires_human_approval":True,"manual_confirmation_completed":bool(self.config.manual_confirmation_completed),"account_masked":True}
        if warnings:
            payload["warnings"] = warnings
        return payload
    def _blocked(self, gate: str) -> dict:
        return {**self.get_status(), "gate": gate, "query_attempted": False, "message": "account readonly query disabled by safety gate"}
    def _failure(self, status: str, message: str) -> dict:
        return {**self.get_status(), "ok": False, "status": status, "error_message": message, "mock_data": False, "read_only": True, "order_submit_enabled": False, "order_cancel_enabled": False, "real_order_submitted": False, "no_order_submitted": True}
    def _ensure_real_client(self) -> bool:
        if self.trader is not None:
            return True
        if not self.config.allow_import_xttrader:
            return False
        from qmt_gateway.trade_readonly_client import QmtTradeReadonlyClient
        cfg = {"account_id": os.getenv("QMT_ACCOUNT_ID", ""), "qmt_userdata_path": os.getenv("QMT_USERDATA_PATH", "")}
        client = QmtTradeReadonlyClient(cfg)
        if self.config.allow_connect_trade_session:
            res = client.connect()
            if not res.get("ok"):
                raise RuntimeError("MiniQMT 未登录 / 交易会话连接失败 / 账号配置缺失 / xttrader 初始化失败: " + "; ".join(res.get("errors") or []))
        self.trader = client
        self.account = None
        return True
    def query_account_asset(self) -> dict:
        if not (self.config.enabled and self.config.read_only and self.config.manual_confirmation_completed and self.config.allow_account_query):
            return self._blocked("account_asset")
        limited = self.rate_limiter.allow()
        if limited["status"] != "PASS":
            return limited
        try:
            if not self._ensure_real_client():
                return {"status":"SUCCESS","mock_data":True,"read_only":True,"account_masked":True,"asset":{"account_id_masked":"91****91","cash":0.0,"available_cash":0.0,"total_asset":0.0,"market_value":0.0,"account_masked":True,"read_only":True,"order_submit_enabled":False},"order_submit_enabled":False,"real_order_submitted":False,"no_order_submitted":True}
            fn = getattr(self.trader, "query_stock_asset", None) or getattr(self.trader, "query_asset", None)
            data = fn(self.account) if self.account is not None else fn()
            if isinstance(data, dict) and data.get("error"):
                return self._failure("ACCOUNT_QUERY_FAILED", str(data.get("error")))
        except Exception as exc:
            return self._failure("ACCOUNT_QUERY_FAILED", str(exc))
        asset = mask_payload(data)
        if isinstance(asset, dict):
            account_id = asset.pop("account_id", None) or asset.pop("account_no", None) or asset.pop("account", None)
            if account_id is not None:
                asset["account_id_masked"] = account_id
                asset["account_id"] = account_id
            asset.update({"account_masked":True,"read_only":True,"order_submit_enabled":False})
        return {"status":"SUCCESS","mock_data":False,"read_only":True,"account_masked":True,"asset":asset,"order_submit_enabled":False,"real_order_submitted":False,"no_order_submitted":True}
    def query_positions(self) -> dict:
        if not (self.config.enabled and self.config.read_only and self.config.manual_confirmation_completed and self.config.allow_position_query):
            return self._blocked("positions")
        limited = self.rate_limiter.allow()
        if limited["status"] != "PASS":
            return limited
        try:
            if not self._ensure_real_client():
                positions=[{"symbol":"510300.SH","name":"沪深300ETF","volume":100,"available_volume":0,"cost_price":0,"latest_price":0,"market_value":0,"floating_pnl":0,"read_only":True}]
                return {"status":"SUCCESS","mock_data":True,"read_only":True,"account_masked":True,"positions":positions,"position_count":len(positions),"order_submit_enabled":False,"real_order_submitted":False,"no_order_submitted":True}
            fn = getattr(self.trader, "query_stock_positions", None) or getattr(self.trader, "query_positions", None)
            data = fn(self.account) if self.account is not None else fn()
            data = data if isinstance(data, list) else list(data or [])
            errors = [str(x.get("error")) for x in data if isinstance(x, dict) and x.get("error")]
            if errors:
                return self._failure("POSITION_QUERY_FAILED", "; ".join(errors))
        except Exception as exc:
            return self._failure("POSITION_QUERY_FAILED", str(exc))
        return {"status":"SUCCESS","mock_data":False,"read_only":True,"account_masked":True,"positions":mask_payload(data),"position_count":len(data),"order_submit_enabled":False,"real_order_submitted":False,"no_order_submitted":True}
