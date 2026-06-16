# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime, json, os
from .risk_config import load_risk_config

def build_risk_report(cfg, risk_result=None, signal=None):
    rc = load_risk_config(cfg or {})
    risk_result = risk_result or {}; signal = signal or risk_result.get("raw_signal") or {}
    raw_full = float(signal.get("raw_target_position_pct", signal.get("target_position_pct") or 0) or 0) >= 1.0
    return {"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "exists_100pct_raw_signal": raw_full,
            "approved_target_position_pct": risk_result.get("approved_target_position_pct"), "max_total_position_pct": rc.get("max_total_position_pct"),
            "max_symbol_position_pct": rc.get("max_symbol_position_pct"), "max_daily_loss_pct": rc.get("max_daily_loss_pct"), "max_weekly_loss_pct": rc.get("max_weekly_loss_pct"),
            "max_drawdown_stop_pct": rc.get("max_drawdown_stop_pct"), "max_trades_per_day": rc.get("max_trades_per_day"),
            "cooldown_triggered": False, "drawdown_stop_triggered": False, "manual_confirm_required": rc.get("force_manual_confirm", True),
            "trade_rejected": bool(risk_result.get("risk_rejections")), "rejection_reasons": risk_result.get("risk_rejections", []),
            "live_trading_allowed": False, "small_capital_live_allowed": False,
            "live_gate_reasons": ["live_trading_enabled=false", "daily dry-run 未满 20 个交易日", "Risk Engine 尚未完全验收", "仍存在年度回撤/过拟合/集中度风险"]}

def write_risk_report(report, reports_dir="reports"):
    if not os.path.isdir(reports_dir): os.makedirs(reports_dir)
    path = os.path.join(reports_dir, "latest_risk_report.json")
    with open(path, "w", encoding="utf-8") as h: json.dump(report, h, ensure_ascii=False, indent=2)
    md = os.path.join(reports_dir, "latest_risk_report.md")
    with open(md, "w", encoding="utf-8") as h:
        h.write("# 风控验收报告\n\n- 当前是否允许实盘：否\n- 当前是否允许小资金实盘：否\n- 是否需要人工确认：%s\n- 是否拒绝交易：%s\n- 拒绝原因：%s\n" % ("是" if report.get("manual_confirm_required") else "否", "是" if report.get("trade_rejected") else "否", "；".join(report.get("rejection_reasons") or [])))
    return path
