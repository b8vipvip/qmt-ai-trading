# -*- coding: utf-8 -*-
# qmt_config.py
# 统一读取 D:\AI\qmt\config.json

import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise RuntimeError("配置文件不存在: {0}".format(CONFIG_FILE))

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    required_keys = [
        "qmt_python_exe",
        "qmt_userdata_path",
        "account_id",
        "stock_code",
        "period",
        "fast_ma",
        "slow_ma",
        "allowed_stocks",
        "lot_size",
        "max_single_order_value",
        "max_order_amount",
        "min_order_value",
        "live_trading_enabled",
        "paths",
        "daily_scripts"
    ]

    for key in required_keys:
        if key not in cfg:
            raise RuntimeError("config.json 缺少字段: {0}".format(key))

    if cfg["account_id"] == "你的资金账号":
        raise RuntimeError("请先在 config.json 里填写真实资金账号。")

    if not os.path.exists(cfg["qmt_python_exe"]):
        raise RuntimeError("qmt_python_exe 不存在: {0}".format(cfg["qmt_python_exe"]))

    if not os.path.exists(cfg["qmt_userdata_path"]):
        raise RuntimeError("qmt_userdata_path 不存在: {0}".format(cfg["qmt_userdata_path"]))

    paths = cfg["paths"]
    for key in ["target_signal_file", "order_plan_file", "signals_dir", "backtest_results_dir"]:
        if key not in paths:
            raise RuntimeError("config.json paths 缺少字段: {0}".format(key))

    if cfg["stock_code"] not in cfg["allowed_stocks"]:
        raise RuntimeError("stock_code 不在 allowed_stocks 中，请检查配置。")

    if bool(cfg["live_trading_enabled"]):
        raise RuntimeError("当前阶段禁止 live_trading_enabled=true，请保持 false。")

    return cfg