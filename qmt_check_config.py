# -*- coding: utf-8 -*-
# qmt_check_config.py
# 检查 config.json 是否可用，不连接QMT，不下单

import os
from qmt_config import load_config


def main():
    print("=== QMT config check ===")

    cfg = load_config()

    print("[OK] config.json 加载成功")
    print("qmt_python_exe:", cfg["qmt_python_exe"])
    print("qmt_userdata_path:", cfg["qmt_userdata_path"])
    print("stock_code:", cfg["stock_code"])
    print("period:", cfg["period"])
    print("fast_ma:", cfg["fast_ma"])
    print("slow_ma:", cfg["slow_ma"])
    print("allowed_stocks:", cfg["allowed_stocks"])
    print("live_trading_enabled:", cfg["live_trading_enabled"])

    for name, path in cfg["paths"].items():
        print("path.{0}: {1}".format(name, path))

    print("\n--- daily scripts ---")
    for script in cfg["daily_scripts"]:
        exists = os.path.exists(script)
        print("[OK]" if exists else "[MISSING]", script)

    print("\n[OK] 配置检查完成。")


if __name__ == "__main__":
    main()