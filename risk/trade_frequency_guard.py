# -*- coding: utf-8 -*-
def frequency_rejections(context, cfg, signal):
    rejections=[]
    if int((context or {}).get("trades_today", 0) or 0) >= int(cfg.get("max_trades_per_day", 999)):
        rejections.append("超过单日交易次数限制")
    if signal.get("signal") == "BUY_SIGNAL" and not cfg.get("allow_buy_after_sell_same_day", False) and (context or {}).get("sold_today"):
        rejections.append("同日卖出后禁止再买入")
    return rejections
