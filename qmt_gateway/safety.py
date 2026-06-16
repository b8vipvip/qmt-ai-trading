# -*- coding: utf-8 -*-
from __future__ import absolute_import
import re

TRADE_CALLS = ("order_stock", "cancel_order_stock")
DISABLED_EXECUTOR_PATH = "qmt_gateway/trade_executor_disabled.py"
REJECTION_WORDS = ("禁用", "disabled", "refused", "拒绝")


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


def _strip_line_literals_and_comments(line):
    code_only = re.sub(r"#.*$", "", line or "")
    code_only = re.sub(r'"(?:\\.|[^"\\])*"', '""', code_only)
    code_only = re.sub(r"'(?:\\.|[^'\\])*'", "''", code_only)
    return code_only


def _line_has_trade_call(line):
    return re.search(r"\b(order_stock|cancel_order_stock)\s*\(", _strip_line_literals_and_comments(line or "")) is not None


def _disabled_executor_method_is_rejecting(source_text, method_name):
    pattern = re.compile(r"(?m)^\s*def\s+%s\s*\([^\n]*\):" % re.escape(method_name))
    match = pattern.search(source_text or "")
    if not match:
        return False
    lines = (source_text or "").splitlines()
    def_line_index = (source_text[:match.start()].count("\n"))
    body = "\n".join(lines[def_line_index + 1:def_line_index + 8])
    body_lower = body.lower()
    return (
        "raise" in body_lower and
        "runtimeerror" in body_lower and
        any(word.lower() in body_lower for word in REJECTION_WORDS)
    )


def scan_source_text_for_trade_call_violations(relative_path, source_text):
    """Return line-numbered safety violations for real trade call references.

    Tests are allowed to contain safety keywords. The disabled executor may only
    define rejecting order/cancel methods; all other source files must not
    contain direct trade call syntax.
    """
    rel = (relative_path or "").replace("\\", "/")
    text = source_text or ""
    if rel.startswith("tests/"):
        return []
    if rel == DISABLED_EXECUTOR_PATH:
        violations = []
        for name in TRADE_CALLS:
            if not _disabled_executor_method_is_rejecting(text, name):
                violations.append("%s:0: %s 必须只抛出 RuntimeError 拒绝交易" % (rel, name))
        for index, line in enumerate(text.splitlines(), 1):
            if _line_has_trade_call(line) and not re.match(r"^\s*def\s+(order_stock|cancel_order_stock)\s*\(", line):
                violations.append("%s:%s: %s" % (rel, index, line.strip()))
        return violations
    violations = []
    for index, line in enumerate(text.splitlines(), 1):
        if _line_has_trade_call(line):
            violations.append("%s:%s: %s" % (rel, index, line.strip()))
    return violations


def validate_allowed_stock(stock_code, allowed_stocks):
    if stock_code and stock_code not in (allowed_stocks or []):
        raise RuntimeError("stock_code 不在 allowed_stocks 中: %s" % stock_code)
    return True


def validate_config_safe(cfg):
    assert_live_disabled(cfg)
    account = (cfg or {}).get("account_id")
    return {"live_trading_enabled": False, "account_id_masked": redact_account_id(account)}
