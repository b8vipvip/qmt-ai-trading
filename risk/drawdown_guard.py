# -*- coding: utf-8 -*-
def drawdown_rejections(context, cfg):
    rejections=[]
    if float((context or {}).get("daily_loss_pct", 0) or 0) <= -float(cfg.get("max_daily_loss_pct", 1)):
        rejections.append("触发单日亏损限制")
    if float((context or {}).get("weekly_loss_pct", 0) or 0) <= -float(cfg.get("max_weekly_loss_pct", 1)):
        rejections.append("触发单周亏损限制")
    if float((context or {}).get("max_drawdown_pct", 0) or 0) >= float(cfg.get("max_drawdown_stop_pct", 1)):
        rejections.append("触发最大回撤熔断")
    return rejections
