# -*- coding: utf-8 -*-
from __future__ import absolute_import
DEFAULT_RISK_CONFIG = {"enabled": True, "max_total_position_pct": 0.5, "max_symbol_position_pct": 0.2, "max_daily_loss_pct": 0.02, "max_weekly_loss_pct": 0.05, "max_drawdown_stop_pct": 0.12, "cooldown_days_after_loss": 2, "max_trades_per_day": 2, "allow_buy_after_sell_same_day": False, "force_manual_confirm": True, "live_initial_capital_pct": 0.05, "shadow_max_total_position_pct": 0.7, "shadow_max_symbol_position_pct": 0.5}
def load_risk_config(cfg, mode="dryrun"):
    data = dict(DEFAULT_RISK_CONFIG); data.update((cfg or {}).get("risk_engine") or {})
    if mode == "shadow":
        data["max_total_position_pct"] = data.get("shadow_max_total_position_pct", data["max_total_position_pct"])
        data["max_symbol_position_pct"] = data.get("shadow_max_symbol_position_pct", data["max_symbol_position_pct"])
    return data
