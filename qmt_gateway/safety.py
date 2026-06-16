# -*- coding: utf-8 -*-
from __future__ import absolute_import
import re

TRADE_CALLS = ("order_stock", "cancel_order_stock")

def redact_account_id(account_id):
    text = "" if account_id is None else str(account_id)
    return text[:2] + "***" + text[-2:] if len(text) >= 4 else "***"

def redact_secret(value):
    if value is None:
        return None
    return "***"

def assert_live_disabled(cfg):
    if bool((cfg or {}).get("live_trading_enabled", False)):
        raise RuntimeError("当前阶段禁止 live_trading_enabled=true，请保持 false。")
    return True

def assert_no_trade_functions_called(source_text):
    text = source_text or ""
    for name in TRADE_CALLS:
        if re.search(r"\.%s\s*\(" % name, text):
            raise RuntimeError("发现真实交易函数调用风险: %s" % name)
    return True

def validate_allowed_stock(stock_code, allowed_stocks):
    if stock_code and stock_code not in (allowed_stocks or []):
        raise RuntimeError("stock_code 不在 allowed_stocks 中: %s" % stock_code)
    return True

def validate_config_safe(cfg):
    assert_live_disabled(cfg)
    account = (cfg or {}).get("account_id")
    return {"live_trading_enabled": False, "account_id_masked": redact_account_id(account)}
