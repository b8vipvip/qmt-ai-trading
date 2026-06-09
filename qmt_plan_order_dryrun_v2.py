# -*- coding: utf-8 -*-
# qmt_plan_order_dryrun_v2.py
# 从 config.json 读取参数
# 读取信号 + 查询账户 + 生成计划文件
# 安全说明：不下单、不撤单、不调用 order_stock、不调用 cancel_order_stock

import json
import os
import sys
from datetime import datetime
from xtquant.xttrader import XtQuantTrader, XtQuantTraderCallback
from xtquant.xttype import StockAccount
from qmt_config import load_config


class DryRunCallback(XtQuantTraderCallback):
    def on_disconnected(self):
        print("connection lost")


def load_json(path):
    if not os.path.exists(path):
        raise RuntimeError("文件不存在: {0}".format(path))

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_position_volume(positions, stock_code):
    if not positions:
        return 0

    for p in positions:
        if p.stock_code == stock_code:
            return int(p.volume)

    return 0


def round_to_lot(volume, lot_size):
    return int(volume / lot_size) * lot_size


def build_plan(cfg, signal, asset, positions):
    stock_code = signal["stock_code"]
    signal_type = signal["signal"]
    target_position_pct = signal["target_position_pct"]
    last_close = float(signal["last_close"])

    lot_size = int(cfg["lot_size"])
    max_single_order_value = float(cfg["max_single_order_value"])
    min_order_value = float(cfg["min_order_value"])

    total_asset = float(asset.total_asset)
    cash = float(asset.cash)

    current_volume = get_position_volume(positions, stock_code)
    current_value = current_volume * last_close

    plan = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "DRY_RUN",
        "safety_note": "本文件只是计划，不代表已下单。本脚本没有调用任何下单/撤单接口。",
        "stock_code": stock_code,
        "signal": signal_type,
        "signal_reason": signal.get("reason", ""),
        "last_close": last_close,
        "target_position_pct": target_position_pct,
        "account": {
            "total_asset": total_asset,
            "cash": cash,
            "current_volume": current_volume,
            "current_value_by_last_close": current_value
        },
        "target": {},
        "action": "NONE",
        "plan_side": "NONE",
        "plan_volume": 0,
        "plan_price_ref": last_close,
        "plan_amount": 0.0,
        "warnings": []
    }

    if signal_type == "HOLD" or target_position_pct is None:
        plan["action"] = "HOLD"
        plan["warnings"].append("信号为HOLD，不生成买卖计划。")
        return plan

    target_value = total_asset * float(target_position_pct)
    diff_value = target_value - current_value

    plan["target"] = {
        "target_value": target_value,
        "diff_value": diff_value
    }

    if signal_type == "BUY_SIGNAL":
        if diff_value <= 0:
            plan["action"] = "NO_ACTION"
            plan["warnings"].append("当前持仓已达到或超过目标仓位，无需买入。")
            return plan

        if diff_value > max_single_order_value:
            plan["warnings"].append("计划买入金额超过单次上限，已按上限计算。")
            diff_value = max_single_order_value

        buy_volume = round_to_lot(diff_value / last_close, lot_size)
        buy_amount = buy_volume * last_close

        if buy_volume <= 0 or buy_amount < min_order_value:
            plan["action"] = "NO_ACTION"
            plan["warnings"].append("买入金额过小，暂不交易。")
            return plan

        if buy_amount > cash:
            plan["warnings"].append("现金不足，按可用现金重新计算。")
            buy_volume = round_to_lot(cash / last_close, lot_size)
            buy_amount = buy_volume * last_close

        if buy_volume <= 0:
            plan["action"] = "NO_ACTION"
            plan["warnings"].append("可用现金不足一手，无法生成买入计划。")
            return plan

        plan["action"] = "PLAN_BUY"
        plan["plan_side"] = "BUY"
        plan["plan_volume"] = buy_volume
        plan["plan_amount"] = buy_amount
        return plan

    if signal_type == "SELL_SIGNAL":
        if current_volume <= 0:
            plan["action"] = "NO_ACTION"
            plan["warnings"].append("当前无持仓，SELL_SIGNAL 无需操作。")
            return plan

        sell_volume = round_to_lot(current_volume, lot_size)
        sell_amount = sell_volume * last_close

        if sell_volume <= 0:
            plan["action"] = "NO_ACTION"
            plan["warnings"].append("可卖数量不足一手，暂不交易。")
            return plan

        plan["action"] = "PLAN_SELL"
        plan["plan_side"] = "SELL"
        plan["plan_volume"] = sell_volume
        plan["plan_amount"] = sell_amount
        return plan

    plan["action"] = "NO_ACTION"
    plan["warnings"].append("未知信号类型，不生成交易计划。")
    return plan


def main():
    cfg = load_config()

    qmt_userdata_path = cfg["qmt_userdata_path"]
    account_id = cfg["account_id"]

    default_signal_file = cfg["paths"]["target_signal_file"]
    order_plan_file = cfg["paths"]["order_plan_file"]
    out_dir = os.path.dirname(order_plan_file)
    os.makedirs(out_dir, exist_ok=True)

    signal_file = default_signal_file
    if len(sys.argv) >= 2:
        signal_file = sys.argv[1]

    print("=== QMT dry-run order plan v2 ===")
    print("信号文件:", signal_file)
    print("注意：本脚本只生成计划文件，不执行任何实盘交易。")

    signal = load_json(signal_file)

    trader = XtQuantTrader(qmt_userdata_path, 100003)
    trader.register_callback(DryRunCallback())
    trader.start()

    connect_result = trader.connect()
    print("connect_result:", connect_result)

    if connect_result != 0:
        print("连接失败。请确认 MiniQMT 已登录，userdata_mini 路径正确。")
        return

    acc = StockAccount(account_id, "STOCK")

    subscribe_result = trader.subscribe(acc)
    print("subscribe_result:", subscribe_result)

    asset = trader.query_stock_asset(acc)
    positions = trader.query_stock_positions(acc)

    if not asset:
        print("资金查询失败，停止生成计划。")
        return

    plan = build_plan(cfg, signal, asset, positions)
    save_json(order_plan_file, plan)

    print("\n=== PLAN RESULT ===")
    print("stock_code:", plan["stock_code"])
    print("signal:", plan["signal"])
    print("action:", plan["action"])
    print("plan_side:", plan["plan_side"])
    print("plan_volume:", plan["plan_volume"])
    print("plan_price_ref:", plan["plan_price_ref"])
    print("plan_amount:", round(plan["plan_amount"], 2))

    if plan["warnings"]:
        print("\n--- warnings ---")
        for w in plan["warnings"]:
            print("-", w)

    print("\n计划文件:", order_plan_file)
    print("注意：这里只是生成计划，没有下单。")


if __name__ == "__main__":
    main()