# -*- coding: utf-8 -*-
# qmt_execute_manual_guard.py
# 从 config.json 读取参数
# 人工确认执行器：安全预检版
# 当前版本不会下单，不调用 order_stock，只做计划检查

import json
import os
from datetime import datetime
from qmt_config import load_config


def load_json(path):
    if not os.path.exists(path):
        raise RuntimeError("计划文件不存在: {0}".format(path))

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def reject(reason):
    print("\n[ERROR] 拒绝执行:", reason)
    print("没有执行任何交易。")
    raise SystemExit(1)


def main():
    cfg = load_config()

    order_plan_file = cfg["paths"]["order_plan_file"]
    allowed_stocks = cfg["allowed_stocks"]
    max_order_amount = float(cfg["max_order_amount"])
    live_trading_enabled = bool(cfg["live_trading_enabled"])

    print("=== QMT manual execute guard ===")
    print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("计划文件:", order_plan_file)
    print("当前版本：安全预检版，不会下单。")

    plan = load_json(order_plan_file)

    stock_code = plan.get("stock_code")
    action = plan.get("action")
    side = plan.get("plan_side")
    volume = int(plan.get("plan_volume", 0))
    amount = float(plan.get("plan_amount", 0))
    price = float(plan.get("plan_price_ref", 0))
    signal_reason = plan.get("signal_reason", "")

    print("\n--- plan ---")
    print("stock_code:", stock_code)
    print("action:", action)
    print("side:", side)
    print("volume:", volume)
    print("price_ref:", price)
    print("amount:", round(amount, 2))
    print("reason:", signal_reason)

    # 1. 拒绝测试信号
    if "测试" in signal_reason or "TEST" in signal_reason.upper():
        reject("这是测试信号生成的计划，不能用于实盘。")

    # 2. 只允许指定标的
    if stock_code not in allowed_stocks:
        reject("标的不在允许列表中。")

    # 3. 没有操作就直接退出
    if action in ["NO_ACTION", "HOLD", "NONE"]:
        print("\n[OK] 当前计划无需交易。")
        print("没有执行任何交易。")
        return

    # 4. 只允许 PLAN_BUY / PLAN_SELL
    if action not in ["PLAN_BUY", "PLAN_SELL"]:
        reject("未知 action，停止。")

    # 5. 检查方向
    if side not in ["BUY", "SELL"]:
        reject("未知买卖方向，停止。")

    # 6. 检查数量
    if volume <= 0:
        reject("计划数量小于等于0。")

    if volume % int(cfg["lot_size"]) != 0:
        reject("计划数量不是 lot_size 的整数倍。")

    # 7. 检查金额
    if amount <= 0:
        reject("计划金额小于等于0。")

    if amount > max_order_amount:
        reject("计划金额超过单笔保护上限。")

    # 8. 当前版本不允许实盘
    if not live_trading_enabled:
        print("\n[OK] 预检通过，但当前 live_trading_enabled = false")
        print("所以这里只打印计划，不会下单。")
        print("\n未来进入实盘版前，还需要加入：")
        print("1. 交易时间检查")
        print("2. 最新价检查")
        print("3. 涨跌停检查")
        print("4. 人工输入 YES_EXECUTE")
        print("5. order_stock 下单")
        print("6. 委托回报和废单处理")
        return

    reject("当前版本不开放实盘下单。")


if __name__ == "__main__":
    main()