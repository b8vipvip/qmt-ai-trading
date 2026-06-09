# -*- coding: utf-8 -*-
# qmt_stable_ma.py
# 多参数 + 多时间段稳定性筛选：只读行情 + 本地回测，不下单

import csv
import json
import os
from xtquant import xtdata


INITIAL_CASH = 100000.0
STOCK_CODE = "510300.SH"
PERIOD = "1d"

COMMISSION_RATE = 0.0001
MIN_COMMISSION = 5.0
STAMP_TAX_SELL = 0.0   # ETF 不收印花税；普通股票可改为 0.0005
LOT_SIZE = 100

FAST_LIST = [3, 5, 8, 10, 13, 20, 30]
SLOW_LIST = [15, 20, 30, 40, 60, 90, 120]

VALIDATE_PERIODS = [
    ("20230101", "20231231"),
    ("20240101", "20241231"),
    ("20250101", "20251231"),
    ("20260101", "20260609"),
    ("20230101", "20260609"),
]

OUT_DIR = r"D:\AI\qmt\backtest_results"
RESULT_JSON = os.path.join(OUT_DIR, "stable-ma-result.json")
RESULT_CSV = os.path.join(OUT_DIR, "stable-ma-result.csv")
BEST_JSON = os.path.join(OUT_DIR, "stable-ma-best.json")


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


def run_backtest(dates, closes, fast_ma, slow_ma):
    fast = calc_ma(closes, fast_ma)
    slow = calc_ma(closes, slow_ma)

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
                        "commission": commission
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
                "stamp_tax": stamp_tax
            })
            position = 0

    final_equity = cash + position * float(closes[-1])
    profit = final_equity - INITIAL_CASH
    profit_rate = profit / INITIAL_CASH
    max_dd = calc_max_drawdown(equity_curve)

    return {
        "final_equity": final_equity,
        "profit": profit,
        "profit_rate": profit_rate,
        "max_drawdown": max_dd,
        "trade_count": len(trades),
        "position_left": position
    }


def score_parameter(period_results):
    """
    稳定性评分：
    1. 年度赚钱次数越多越好
    2. 整体收益越高越好
    3. 最大回撤越低越好
    4. 年度亏损越少越好
    """

    yearly = period_results[:4]
    full = period_results[-1]

    positive_years = 0
    worst_year_profit = 999
    worst_drawdown = 0
    total_year_profit = 0

    for r in yearly:
        pr = r["profit_rate"]
        dd = r["max_drawdown"]

        if pr > 0:
            positive_years += 1

        if pr < worst_year_profit:
            worst_year_profit = pr

        if dd > worst_drawdown:
            worst_drawdown = dd

        total_year_profit += pr

    full_profit = full["profit_rate"]
    full_drawdown = full["max_drawdown"]

    # 简单评分，可后续继续优化
    score = 0
    score += positive_years * 100
    score += full_profit * 100
    score += total_year_profit * 30
    score -= full_drawdown * 80
    score -= worst_drawdown * 50

    # 惩罚年度严重亏损
    if worst_year_profit < -0.10:
        score -= 50
    elif worst_year_profit < -0.05:
        score -= 25

    return {
        "score": score,
        "positive_years": positive_years,
        "worst_year_profit": worst_year_profit,
        "worst_drawdown": worst_drawdown,
        "full_profit": full_profit,
        "full_drawdown": full_drawdown
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("=== 多参数稳定性筛选 ===")
    print("标的:", STOCK_CODE)

    # 先缓存各时间段K线，避免重复下载读取
    period_data = {}
    for start_time, end_time in VALIDATE_PERIODS:
        print("准备数据:", start_time, "-", end_time)
        dates, closes = get_close_data(start_time, end_time)
        period_data[(start_time, end_time)] = (dates, closes)

    all_results = []

    for fast_ma in FAST_LIST:
        for slow_ma in SLOW_LIST:
            if fast_ma >= slow_ma:
                continue

            period_results = []

            for start_time, end_time in VALIDATE_PERIODS:
                dates, closes = period_data[(start_time, end_time)]

                if len(closes) < slow_ma + 5:
                    continue

                r = run_backtest(dates, closes, fast_ma, slow_ma)
                r["start_time"] = start_time
                r["end_time"] = end_time
                period_results.append(r)

            if len(period_results) != len(VALIDATE_PERIODS):
                continue

            s = score_parameter(period_results)

            row = {
                "stock_code": STOCK_CODE,
                "fast_ma": fast_ma,
                "slow_ma": slow_ma,
                "score": s["score"],
                "positive_years": s["positive_years"],
                "worst_year_profit": s["worst_year_profit"],
                "worst_drawdown": s["worst_drawdown"],
                "full_profit": s["full_profit"],
                "full_drawdown": s["full_drawdown"],
                "period_results": period_results
            }

            all_results.append(row)

            print(
                "fast={0}, slow={1}, score={2:.2f}, 年度盈利={3}/4, "
                "最差年度={4:.2f}%, 整体收益={5:.2f}%, 整体回撤={6:.2f}%".format(
                    fast_ma,
                    slow_ma,
                    s["score"],
                    s["positive_years"],
                    s["worst_year_profit"] * 100,
                    s["full_profit"] * 100,
                    s["full_drawdown"] * 100
                )
            )

    all_results_sorted = sorted(all_results, key=lambda x: x["score"], reverse=True)
    best = all_results_sorted[0] if all_results_sorted else None

    with open(RESULT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_results_sorted, f, ensure_ascii=False, indent=2)

    with open(BEST_JSON, "w", encoding="utf-8") as f:
        json.dump(best, f, ensure_ascii=False, indent=2)

    with open(RESULT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank",
            "fast_ma",
            "slow_ma",
            "score",
            "positive_years",
            "worst_year_profit_pct",
            "worst_drawdown_pct",
            "full_profit_pct",
            "full_drawdown_pct"
        ])

        for idx, r in enumerate(all_results_sorted, 1):
            writer.writerow([
                idx,
                r["fast_ma"],
                r["slow_ma"],
                round(r["score"], 4),
                r["positive_years"],
                round(r["worst_year_profit"] * 100, 4),
                round(r["worst_drawdown"] * 100, 4),
                round(r["full_profit"] * 100, 4),
                round(r["full_drawdown"] * 100, 4)
            ])

    print("\n=== 稳定性筛选完成 ===")

    if best:
        print("最佳稳定参数:")
        print("fast_ma:", best["fast_ma"])
        print("slow_ma:", best["slow_ma"])
        print("score:", round(best["score"], 2))
        print("年度盈利数量:", best["positive_years"], "/ 4")
        print("最差年度收益:", round(best["worst_year_profit"] * 100, 2), "%")
        print("最大年度回撤:", round(best["worst_drawdown"] * 100, 2), "%")
        print("整体收益:", round(best["full_profit"] * 100, 2), "%")
        print("整体回撤:", round(best["full_drawdown"] * 100, 2), "%")

    print("\n结果文件:")
    print(RESULT_JSON)
    print(RESULT_CSV)
    print(BEST_JSON)
    print("\n注意：本脚本只做本地回测筛选，没有执行任何实盘交易。")


if __name__ == "__main__":
    main()