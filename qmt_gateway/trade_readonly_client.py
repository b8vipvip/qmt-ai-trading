# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .snapshot import build_account_snapshot
from .safety import redact_account_id, validate_config_safe

class QmtTradeReadonlyClient(object):
    def __init__(self, cfg):
        self.cfg = cfg or {}; validate_config_safe(self.cfg)
        self.trader = None; self.account = None; self.connected = False; self.errors = []
    def _load_classes(self):
        try:
            from xtquant.xttrader import XtQuantTrader
            from xtquant.xttype import StockAccount
            return XtQuantTrader, StockAccount
        except Exception as exc:
            raise RuntimeError("QMT只读交易模块不可用，请在Windows MiniQMT Python环境运行: %s" % exc)
    def connect(self):
        try:
            XtQuantTrader, StockAccount = self._load_classes()
            self.trader = XtQuantTrader(self.cfg.get("qmt_userdata_path"), 100003)
            self.trader.start()
            result = self.trader.connect()
            if result != 0:
                self.errors.append("connect_result=%s，MiniQMT连接失败" % result)
                return {"ok": False, "connect_result": result, "account_id_masked": redact_account_id(self.cfg.get("account_id")), "errors": list(self.errors)}
            self.account = StockAccount(self.cfg.get("account_id"), "STOCK")
            sub = self.trader.subscribe(self.account)
            self.connected = True
            return {"ok": True, "connect_result": result, "subscribe_result": sub, "account_id_masked": redact_account_id(self.cfg.get("account_id")), "errors": []}
        except Exception as exc:
            self.errors.append(str(exc))
            return {"ok": False, "account_id_masked": redact_account_id(self.cfg.get("account_id")), "errors": list(self.errors)}
    def _ensure(self):
        if not self.connected:
            res = self.connect()
            if not res.get("ok"):
                raise RuntimeError("QMT只读连接失败: %s" % "; ".join(res.get("errors") or []))
    def query_asset(self):
        try:
            self._ensure(); return self.trader.query_stock_asset(self.account)
        except Exception as exc:
            return {"error": "资金查询失败: %s" % exc}
    def query_positions(self):
        try:
            self._ensure(); return self.trader.query_stock_positions(self.account) or []
        except Exception as exc:
            return [{"error": "持仓查询失败: %s" % exc}]
    def query_orders(self):
        try:
            self._ensure(); return self.trader.query_stock_orders(self.account) or []
        except Exception as exc:
            return [{"error": "委托查询失败: %s" % exc}]
    def query_trades(self):
        try:
            self._ensure(); return self.trader.query_stock_trades(self.account) or []
        except Exception as exc:
            return [{"error": "成交查询失败: %s" % exc}]
    def get_account_snapshot(self):
        res = self.connect()
        if not res.get("ok"):
            return build_account_snapshot(self.cfg.get("account_id"), {}, [], res.get("errors") or ["QMT连接失败"], [])
        asset = self.query_asset(); positions = self.query_positions()
        errors = []
        if isinstance(asset, dict) and asset.get("error"):
            errors.append(asset.get("error")); asset = {}
        clean_positions = []
        for p in positions or []:
            if isinstance(p, dict) and p.get("error"): errors.append(p.get("error"))
            else: clean_positions.append(p)
        return build_account_snapshot(self.cfg.get("account_id"), asset, clean_positions, errors, [])
