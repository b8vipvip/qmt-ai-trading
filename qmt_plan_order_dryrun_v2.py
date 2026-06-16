# -*- coding: utf-8 -*-
# qmt_plan_order_dryrun_v2.py
# 读取信号 + 只读账户快照 + Risk Engine + 生成计划文件
# 安全说明：不下单、不撤单、不调用真实交易接口

from __future__ import print_function
import json
import os
import sys
from datetime import datetime
from qmt_config import load_config
from qmt_gateway.gateway import QmtGateway
from risk.risk_engine import RiskEngine


def load_json(path):
    if not os.path.exists(path):
        raise RuntimeError("文件不存在: {0}".format(path))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_position_volume(positions, stock_code):
    for p in positions or []:
        code = p.get("stock_code") if isinstance(p, dict) else getattr(p, "stock_code", None)
        if code == stock_code:
            return int((p.get("volume") if isinstance(p, dict) else getattr(p, "volume", 0)) or 0)
    return 0


def round_to_lot(volume, lot_size):
    return int(volume / lot_size) * lot_size


def build_plan(cfg, signal, asset, positions, risk_result=None):
    stock_code = signal.get("stock_code", "")
    signal_type = signal.get("signal")
    last_close = float(signal.get("last_close") or 0)
    lot_size = int(cfg.get("lot_size", 100))
    max_single_order_value = float(cfg.get("max_single_order_value", 0) or 0)
    min_order_value = float(cfg.get("min_order_value", 0) or 0)
    total_asset = float(asset.get("total_asset", 0) or 0)
    cash = float(asset.get("cash", 0) or 0)
    current_volume = get_position_volume(positions, stock_code)
    current_value = current_volume * last_close
    if risk_result is None:
        risk_result = RiskEngine(cfg).evaluate(signal, account=asset, context={})
    target_position_pct = risk_result.get("approved_target_position_pct")
    plan = {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "mode": "DRY_RUN",
        "safety_note": "本文件只是计划，不代表已下单。本脚本没有调用任何下单/撤单接口。",
        "stock_code": stock_code, "signal": signal_type, "signal_reason": signal.get("reason", ""), "last_close": last_close,
        "raw_target_position_pct": signal.get("raw_target_position_pct", signal.get("target_position_pct")),
        "target_position_pct": target_position_pct,
        "account": {"total_asset": total_asset, "cash": cash, "current_volume": current_volume, "current_value_by_last_close": current_value},
        "target": {}, "action": "NONE", "plan_side": "NONE", "plan_volume": 0, "plan_price_ref": last_close, "plan_amount": 0.0,
        "warnings": [], "risk": risk_result, "risk_warnings": risk_result.get("risk_warnings", [])}
    if not risk_result.get("approved", False):
        plan["action"] = "NO_ACTION"; plan["warnings"].append("Risk Engine拒绝交易：" + "；".join(risk_result.get("risk_rejections") or [])); return plan
    if signal_type == "HOLD" or target_position_pct is None or last_close <= 0:
        plan["action"] = "HOLD"; plan["warnings"].append("信号为HOLD或价格无效，不生成买卖计划。") ; return plan
    target_value = total_asset * float(target_position_pct); diff_value = target_value - current_value
    plan["target"] = {"target_value": target_value, "diff_value": diff_value}
    if signal_type == "BUY_SIGNAL":
        if diff_value <= 0:
            plan["action"] = "NO_ACTION"; plan["warnings"].append("当前持仓已达到或超过风控批准目标仓位，无需买入。") ; return plan
        if max_single_order_value and diff_value > max_single_order_value:
            plan["warnings"].append("计划买入金额超过单次上限，已按上限计算。") ; diff_value = max_single_order_value
        diff_value = min(diff_value, cash)
        buy_volume = round_to_lot(diff_value / last_close, lot_size); buy_amount = buy_volume * last_close
        if buy_volume <= 0 or buy_amount < min_order_value:
            plan["action"] = "NO_ACTION"; plan["warnings"].append("买入金额过小或现金不足，暂不交易。") ; return plan
        plan.update({"action": "PLAN_BUY", "plan_side": "BUY", "plan_volume": buy_volume, "plan_amount": buy_amount}); return plan
    if signal_type == "SELL_SIGNAL":
        sell_volume = round_to_lot(current_volume, lot_size); sell_amount = sell_volume * last_close
        if sell_volume <= 0:
            plan["action"] = "NO_ACTION"; plan["warnings"].append("当前无持仓或可卖数量不足一手，暂不交易。") ; return plan
        plan.update({"action": "PLAN_SELL", "plan_side": "SELL", "plan_volume": sell_volume, "plan_amount": sell_amount}); return plan
    plan["action"] = "NO_ACTION"; plan["warnings"].append("未知信号类型，不生成交易计划。") ; return plan


def error_plan(message):
    return {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "mode": "DRY_RUN", "action": "NO_ACTION", "plan_side": "NONE", "plan_volume": 0, "plan_amount": 0.0, "errors": [message], "risk": {"approved": False, "risk_rejections": [message]}}


def main():
    cfg = load_config(); default_signal_file = cfg["paths"]["target_signal_file"]; order_plan_file = cfg["paths"]["order_plan_file"]
    out_dir = os.path.dirname(order_plan_file)
    if out_dir: os.makedirs(out_dir, exist_ok=True)
    signal_file = sys.argv[1] if len(sys.argv) >= 2 else default_signal_file
    print("=== QMT dry-run order plan v2 ==="); print("信号文件:", signal_file); print("注意：本脚本只生成计划文件，不执行任何实盘交易。")
    try:
        signal = load_json(signal_file); gateway = QmtGateway(cfg); snapshot = gateway.trade_readonly.get_account_snapshot()
        if snapshot.get("errors"):
            plan = error_plan("QMT只读账户快照失败: " + "；".join(snapshot.get("errors") or []))
        else:
            risk_result = RiskEngine(cfg).evaluate(signal, account=snapshot.get("asset") or {}, context={})
            plan = build_plan(cfg, signal, snapshot.get("asset") or {}, snapshot.get("positions") or [], risk_result)
        save_json(order_plan_file, plan)
    except Exception as exc:
        plan = error_plan(str(exc)); save_json(order_plan_file, plan)
    print("action:", plan.get("action")); print("plan_amount:", round(float(plan.get("plan_amount", 0) or 0), 2)); print("计划文件:", order_plan_file)
    return plan

if __name__ == "__main__":
    main()
