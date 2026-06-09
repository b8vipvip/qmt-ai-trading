# -*- coding: utf-8 -*-
# qmt_write_daily_status.py
# 读取 target_signal.json + order_plan.json，生成 daily_status.json
# 不连接QMT，不下单

import json
import os
from datetime import datetime
from qmt_config import load_config


def load_json(path):
    if not os.path.exists(path):
        raise RuntimeError("文件不存在: {0}".format(path))

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    cfg = load_config()

    signal_file = cfg["paths"]["target_signal_file"]
    order_plan_file = cfg["paths"]["order_plan_file"]
    daily_status_file = cfg["paths"].get(
        "daily_status_file",
        r"D:\AI\qmt\signals\daily_status.json"
    )

    signal = load_json(signal_file)
    plan = load_json(order_plan_file)

    action = plan.get("action", "UNKNOWN")
    stock_code = plan.get("stock_code", "")
    signal_type = signal.get("signal", "")
    plan_side = plan.get("plan_side", "NONE")
    plan_volume = int(plan.get("plan_volume", 0))
    plan_amount = float(plan.get("plan_amount", 0.0))

    need_manual_review = action in ["PLAN_BUY", "PLAN_SELL"]
    no_action = action in ["NO_ACTION", "HOLD", "NONE"]

    if no_action:
        status = "NO_ACTION"
        message = "今日无需交易。"
    elif need_manual_review:
        status = "NEED_MANUAL_REVIEW"
        message = "今日存在计划委托，需要人工复核。当前系统仍未开启实盘自动交易。"
    else:
        status = "UNKNOWN"
        message = "未知状态，请人工检查信号和计划文件。"

    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "message": message,
        "live_trading_enabled": bool(cfg["live_trading_enabled"]),
        "stock_code": stock_code,
        "signal": {
            "signal": signal_type,
            "reason": signal.get("reason", ""),
            "last_date": signal.get("last_date", ""),
            "last_close": signal.get("last_close", None),
            "fast_ma": signal.get("fast_ma", None),
            "slow_ma": signal.get("slow_ma", None),
            "fast_value": signal.get("fast_value", None),
            "slow_value": signal.get("slow_value", None),
            "target_position_pct": signal.get("target_position_pct", None)
        },
        "order_plan": {
            "action": action,
            "plan_side": plan_side,
            "plan_volume": plan_volume,
            "plan_price_ref": plan.get("plan_price_ref", None),
            "plan_amount": plan_amount,
            "warnings": plan.get("warnings", [])
        },
        "files": {
            "signal_file": signal_file,
            "order_plan_file": order_plan_file,
            "daily_status_file": daily_status_file
        },
        "safety_note": "状态摘要只用于查看，不执行任何交易。"
    }

    save_json(daily_status_file, result)

    print("=== QMT daily status ===")
    print("status:", status)
    print("message:", message)
    print("stock_code:", stock_code)
    print("signal:", signal_type)
    print("action:", action)
    print("plan_side:", plan_side)
    print("plan_volume:", plan_volume)
    print("plan_amount:", round(plan_amount, 2))
    print("daily_status_file:", daily_status_file)
    print("注意：本脚本只生成状态摘要，没有执行任何交易。")


if __name__ == "__main__":
    main()