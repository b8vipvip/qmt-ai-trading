# -*- coding: utf-8 -*-
# qmt_validate_ma.py
# 多时间段验证脚本：只读行情 + 本地回测，不下单

import csv
import json
import os
from xtquant import xtdata


INITIAL_CASH = 100000.0
STOCK_CODE = "510300.SH"
PERIOD = "1d"

# 使用刚才优化出来的最佳参数
FAST_MA = 13
SLOW_MA = 20

# ETF一般无卖出印花税；如果以后测普通股票，再改成 0.0005
COMMISSION_RATE = 0.0001
MIN_COMMISSION = 5.0
STAMP_TAX_SELL = 0.0
LOT_SIZE = 100

OUT_DIR = r"D:\AI\qmt\backtest_results"
RESULT_JSON = os.path.join(OUT_DIR, "validate-result.json")
RESULT_CSV = os.path.join(OUT_DIR, "validate-result.csv")

# 多个验证区间
VALIDATE_PERIODS = [
    ("20230101", "20231231"),
    ("20240101", "20241231"),
    ("20250101", "20251231"),
    ("20260101", "20260609"),
    ("20230101", "20260609"),
    ("20250101", "20260609"),
]


def calc_ma(values, window):
    result = []
    for i in range(len(values)):
        if i + 1 < window:
            result.append(None)
        else:
            result.append(sum(values[i + 1 - window:i + 1]) / window)
    return result


def calc_max_drawdown(equity_curve):
    if not equity_curve:
        return 0.0

    peak = equity_curve[0]
    max_dd = 0.0

    for value in equity_curve:
        if value > peak:
            peak = value
        if peak > 0:
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd

    return max_dd


def run_backtest(dates, closes, start_time, end_time):
    fast = calc_ma(closes, FAST_MA)
    slow = calc_ma(closes, SLOW_MA)

    cash = INITIAL_CASH
    position = 0
    trades = []
    equity_curve = []

    for i in range(len(dates)):
        date = str(dates[i])
        price = float(closes[i])

        equity = cash + position * price
        equity_curve.append(equity)

        if fast[i] is None or slow[i] is None:
            continue

        if fast[i] > slow[i] and position == 0:
            max_shares = int(cash / price / LOT_SIZE) * LOT_SIZE

            if max_shares > 0:
                amount = max_shares * price
                commission = max(amount * COMMISSION_RATE, MIN_COMMISSION)
                total_cost = amount + commission

                if total_cost <= cash:
                    cash -= total_cost
                    position += max_shares
                    trades.append({
                        "date": date,
                        "side": "buy",
                        "price": price,
                        "volume": max_shares,
                        "amount": amount,
                        "commission": commission,
                        "cash_after": cash
                    })

        elif fast[i] < slow[i] and position > 0:
            amount = position * price
            commission = max(amount * COMMISSION_RATE, MIN_COMMISSION)
            stamp_tax = amount * STAMP_TAX_SELL

            cash += amount - commission - stamp_tax

            trades.append({
                "date": date,
                "side": "sell",
                "price": price,
                "volume": position,
                "amount": amount,
                "commission": commission,
                "stamp_tax": stamp_tax,
                "cash_after": cash
            })

            position = 0

    final_equity = cash + position * float(closes[-1])
    profit = final_equity - INITIAL_CASH
    profit_rate = profit / INITIAL_CASH
    max_dd = calc_max_drawdown(equity_curve)

    return {
        "stock_code": STOCK_CODE,
        "period": PERIOD,
        "start_time": start_time,
        "end_time": end_time,
        "fast_ma": FAST_MA,
        "slow_ma": SLOW_MA,
        "initial_cash": INITIAL_CASH,
        "final_equity": final_equity,
        "profit": profit,
        "profit_rate": profit_rate,
        "max_drawdown": max_dd,
        "trade_count": len(trades),
        "position_left": position,
        "trades": trades
    }


def get_close_data(start_time, end_time):
    xtdata.download_history_data(STOCK_CODE, PERIOD, start_time, end_time)

    data = xtdata.get_market_data(
        field_list=["close"],
        stock_list=[STOCK_CODE],
        period=PERIOD,
        start_time=start_time,
        end_time=end_time,
        count=-1,
        dividend_type="front",
        fill_data=True
    )

    close_df = data["close"]
    dates = list(close_df.columns)
    closes = [float(close_df.loc[STOCK_CODE, d]) for d in dates]

    return dates, closes


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("=== 多时间段验证 ===")
    print("标的:", STOCK_CODE)
    print("参数: fast_ma={0}, slow_ma={1}".format(FAST_MA, SLOW_MA))

    results = []

    for start_time, end_time in VALIDATE_PERIODS:
        print("\n验证区间:", start_time, "-", end_time)

        dates, closes = get_close_data(start_time, end_time)

        if len(closes) < SLOW_MA + 5:
            print("K线数量不足，跳过。K线数量:", len(closes))
            continue

        result = run_backtest(dates, closes, start_time, end_time)
        results.append(result)

        print("K线数量:", len(closes))
        print("最终权益:", round(result["final_equity"], 2))
        print("收益:", round(result["profit"], 2))
        print("收益率:", round(result["profit_rate"] * 100, 2), "%")
        print("最大回撤:", round(result["max_drawdown"] * 100, 2), "%")
        print("交易次数:", result["trade_count"])

    with open(RESULT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(RESULT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "stock_code",
            "start_time",
            "end_time",
            "fast_ma",
            "slow_ma",
            "profit_rate",
            "max_drawdown",
            "trade_count",
            "final_equity",
            "profit"
        ])

        for r in results:
            writer.writerow([
                r["stock_code"],
                r["start_time"],
                r["end_time"],
                r["fast_ma"],
                r["slow_ma"],
                round(r["profit_rate"] * 100, 4),
                round(r["max_drawdown"] * 100, 4),
                r["trade_count"],
                round(r["final_equity"], 2),
                round(r["profit"], 2)
            ])

    print("\n=== 验证完成 ===")
    print("结果文件:")
    print(RESULT_JSON)
    print(RESULT_CSV)
    print("\n注意：本脚本只做本地回测验证，没有执行任何实盘交易。")


if __name__ == "__main__":
    main()