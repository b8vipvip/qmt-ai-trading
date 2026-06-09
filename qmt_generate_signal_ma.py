# -*- coding: utf-8 -*-
# qmt_generate_signal_ma.py
# 从 config.json 读取参数，只生成交易信号，不下单、不撤单

import json
import os
from datetime import datetime
from xtquant import xtdata
from qmt_config import load_config


def calc_ma(values, window):
    if len(values) < window:
        return None
    return sum(values[-window:]) / window


def main():
    cfg = load_config()

    stock_code = cfg["stock_code"]
    period = cfg["period"]
    fast_ma = int(cfg["fast_ma"])
    slow_ma = int(cfg["slow_ma"])
    start_time = cfg.get("signal_start_time", "20250101")
    end_time = datetime.now().strftime("%Y%m%d")

    out_file = cfg["paths"]["target_signal_file"]
    out_dir = os.path.dirname(out_file)
    os.makedirs(out_dir, exist_ok=True)

    print("=== 生成均线交易信号 ===")
    print("标的:", stock_code)
    print("参数: fast_ma={0}, slow_ma={1}".format(fast_ma, slow_ma))

    xtdata.download_history_data(stock_code, period, start_time, end_time)

    data = xtdata.get_market_data(
        field_list=["close"],
        stock_list=[stock_code],
        period=period,
        start_time=start_time,
        end_time=end_time,
        count=-1,
        dividend_type="front",
        fill_data=True
    )

    close_df = data["close"]
    dates = list(close_df.columns)
    closes = [float(close_df.loc[stock_code, d]) for d in dates]

    if len(closes) < slow_ma:
        raise RuntimeError("K线数量不足，无法计算均线")

    last_date = str(dates[-1])
    last_close = closes[-1]
    fast_value = calc_ma(closes, fast_ma)
    slow_value = calc_ma(closes, slow_ma)

    if fast_value > slow_value:
        signal = "BUY_SIGNAL"
        target_position_pct = 1.0
        reason = "fast_ma > slow_ma，趋势偏多"
    elif fast_value < slow_value:
        signal = "SELL_SIGNAL"
        target_position_pct = 0.0
        reason = "fast_ma < slow_ma，趋势偏空"
    else:
        signal = "HOLD"
        target_position_pct = None
        reason = "fast_ma 等于 slow_ma，保持观望"

    result = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stock_code": stock_code,
        "period": period,
        "last_date": last_date,
        "last_close": last_close,
        "fast_ma": fast_ma,
        "slow_ma": slow_ma,
        "fast_value": fast_value,
        "slow_value": slow_value,
        "signal": signal,
        "target_position_pct": target_position_pct,
        "reason": reason,
        "safety_note": "本文件只生成信号，不执行任何实盘下单。"
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("日期:", last_date)
    print("收盘价:", last_close)
    print("fast_ma:", round(fast_value, 4))
    print("slow_ma:", round(slow_value, 4))
    print("信号:", signal)
    print("目标仓位:", target_position_pct)
    print("原因:", reason)
    print("信号文件:", out_file)
    print("注意：本脚本只生成信号，没有执行任何交易。")


if __name__ == "__main__":
    main()