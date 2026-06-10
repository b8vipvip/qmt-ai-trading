# -*- coding: utf-8 -*-
"""Load the configurable ETF candidate universe without trading."""
from __future__ import print_function

import json
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


def load_raw_config(config_file=None):
    path = config_file or DEFAULT_CONFIG_FILE
    if not os.path.exists(path):
        raise RuntimeError("[ERROR] 配置文件不存在: {0}".format(path))
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_rotation_config(config_file=None):
    cfg = load_raw_config(config_file)
    rotation = cfg.get("etf_rotation")
    if not isinstance(rotation, dict):
        raise RuntimeError("[ERROR] config.json 缺少 etf_rotation 配置。")
    if bool(cfg.get("live_trading_enabled", False)):
        raise RuntimeError("[ERROR] ETF轮动研究要求 live_trading_enabled 保持为 false。")
    if not rotation.get("enabled", False):
        raise RuntimeError("[ERROR] etf_rotation.enabled 未开启。")
    return cfg, rotation


def load_etf_universe(config_file=None):
    unused, rotation = load_rotation_config(config_file)
    pool = rotation.get("etf_pool") or []
    result = []
    for code in pool:
        code = str(code).strip().upper()
        if code and code not in result:
            result.append(code)
    if not result:
        raise RuntimeError("[ERROR] etf_rotation.etf_pool 为空，请在 config.json 配置 ETF 候选池。")
    return result
