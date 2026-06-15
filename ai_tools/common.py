# -*- coding: utf-8 -*-
from __future__ import print_function

import ast
import json
import os


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN_CALLS = set(["order_stock", "cancel_order_stock", "order_target_volume", "order_target_value"])
FORBIDDEN_IMPORT_PREFIXES = ("xtquant", "requests", "urllib", "subprocess", "socket")
ALLOWED_IMPORTS = set(["collections", "math", "statistics"])
ALLOWED_FUTURE_IMPORTS = set(["print_function"])
DANGEROUS_CALLS = FORBIDDEN_CALLS | set(["open", "exec", "eval", "compile", "__import__", "system", "popen", "remove", "unlink", "rmtree", "urlopen"])
SAFE_CALLS = set(["len", "range", "sum", "min", "max", "abs", "float", "int", "round", "enumerate", "zip", "list", "dict", "set", "append", "get", "items", "values", "sqrt", "mean", "pstdev"])


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, value):
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def resolve_path(path, base_dir=None):
    if os.path.isabs(path):
        return path
    return os.path.join(base_dir or ROOT_DIR, path)


def validate_strategy_source(source):
    """Reject generated strategies that expose trading-side effects."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError("生成策略不是合法 Python: {0}".format(exc))

    has_backtest = False
    has_signal = False
    local_functions = set([node.name for node in tree.body if isinstance(node, ast.FunctionDef)])
    for top_node in tree.body:
        if isinstance(top_node, ast.Expr) and isinstance(top_node.value, (ast.Str,)):
            continue
        if not isinstance(top_node, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef)):
            raise ValueError("生成策略顶层只能包含常量、函数和安全导入")
        if isinstance(top_node, ast.FunctionDef) and (top_node.decorator_list or top_node.returns is not None):
            raise ValueError("生成策略禁止使用装饰器和返回值注解")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_IMPORTS or alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    raise ValueError("生成策略禁止导入模块: {0}".format(alias.name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "__future__":
                if node.level != 0 or any(alias.name not in ALLOWED_FUTURE_IMPORTS for alias in node.names):
                    raise ValueError("生成策略禁止导入模块: {0}".format(module))
                continue
            if module not in ALLOWED_IMPORTS or module.startswith(FORBIDDEN_IMPORT_PREFIXES):
                raise ValueError("生成策略禁止导入模块: {0}".format(module))
        elif isinstance(node, ast.Call):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name in DANGEROUS_CALLS:
                raise ValueError("生成策略包含禁止调用: {0}".format(name))
            if name not in SAFE_CALLS and name not in local_functions:
                raise ValueError("生成策略包含非白名单调用: {0}".format(name))
        elif isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "live_trading_enabled" for target in node.targets):
                if getattr(node.value, "value", None) is not False:
                    raise ValueError("生成策略禁止启用实盘交易")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "backtest":
                has_backtest = True
            if node.name == "generate_signal":
                has_signal = True

    if not has_backtest or not has_signal:
        raise ValueError("生成策略必须同时定义 backtest 和 generate_signal")
    return True
