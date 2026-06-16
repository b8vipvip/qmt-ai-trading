# -*- coding: utf-8 -*-
from __future__ import absolute_import
import datetime
from .risk_config import load_risk_config
from .position_limits import cap_target
from .order_limits import cap_order_amount
from .drawdown_guard import drawdown_rejections
from .trade_frequency_guard import frequency_rejections

class RiskEngine(object):
    def __init__(self, cfg, mode="dryrun"):
        self.cfg = cfg or {}; self.risk_cfg = load_risk_config(cfg, mode); self.mode = mode
    def evaluate(self, signal, account=None, portfolio=None, context=None):
        signal = signal or {}; account = account or {}; portfolio = portfolio or {}; context = context or {}
        total = float(account.get("total_asset", portfolio.get("total_asset", portfolio.get("cash", 0))) or 0)
        cash = float(account.get("cash", portfolio.get("cash", 0)) or 0)
        raw = signal.get("raw_target_position_pct", signal.get("target_position_pct"))
        if raw is None:
            raw = 0.0 if signal.get("signal") == "SELL_SIGNAL" else None
        warnings=[]; adjustments=[]; rejections=[]
        if not self.risk_cfg.get("enabled", True):
            approved_target = float(raw or 0)
        elif signal.get("signal") in ("HOLD", None, "") or raw is None:
            approved_target = None
        else:
            approved_target = cap_target(raw, self.risk_cfg.get("max_symbol_position_pct"), self.risk_cfg.get("max_total_position_pct"))
            if approved_target < float(raw or 0):
                adjustments.append("策略原始目标仓位为 {0}，风控层按仓位上限调整为 {1}".format(raw, approved_target))
        rejections += drawdown_rejections(context, self.risk_cfg)
        rejections += frequency_rejections(context, self.risk_cfg, signal)
        if bool(self.cfg.get("live_trading_enabled", False)):
            rejections.append("live_trading_enabled=true 不符合当前验收门禁")
        if self.risk_cfg.get("force_manual_confirm", True):
            warnings.append("force_manual_confirm=true，任何实盘切换前必须人工确认")
        approved = not rejections
        if signal.get("signal") == "BUY_SIGNAL" and approved_target is not None:
            approved_order_amount = cap_order_amount(total * approved_target, self.cfg.get("max_single_order_value"), cash)
        else:
            approved_order_amount = 0.0
        return {"risk_checked_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "raw_signal": signal, "approved": approved,
                "approved_target_position_pct": approved_target if approved else None, "approved_order_amount": approved_order_amount if approved else 0.0,
                "risk_rejections": rejections, "risk_warnings": warnings, "risk_adjustments": adjustments,
                "risk_config": self.risk_cfg, "manual_confirm_required": bool(self.risk_cfg.get("force_manual_confirm", True))}
